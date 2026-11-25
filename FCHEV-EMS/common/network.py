import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Beta, Normal
from common.fc_action import FCActionPolicy

# Initialize  weights
def weights_init(m):
    if isinstance(m, nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight, gain=1)
        torch.nn.init.constant_(m.bias, 0)


class QNetwork(nn.Module):
    def __init__(self, args):
        super(QNetwork, self).__init__()
        input_dim = args.obs_dim + args.action_dim
        hidden_dim = 256
        # Q1 architecture
        self.linear1 = nn.Linear(input_dim, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, hidden_dim)
        self.linear3 = nn.Linear(hidden_dim, 1)
        
        # Q2 architecture
        self.linear4 = nn.Linear(input_dim, hidden_dim)
        self.linear5 = nn.Linear(hidden_dim, hidden_dim)
        self.linear6 = nn.Linear(hidden_dim, 1)

        # optional LayerNorm on hidden layers (Linear -> LayerNorm -> ReLU) to
        # stabilize critic learning / bound Q-target variance.
        self.use_ln = bool(getattr(args, "critic_layernorm", False))
        if self.use_ln:
            self.ln1 = nn.LayerNorm(hidden_dim)
            self.ln2 = nn.LayerNorm(hidden_dim)
            self.ln4 = nn.LayerNorm(hidden_dim)
            self.ln5 = nn.LayerNorm(hidden_dim)

        # initialize (weights_init only touches nn.Linear; LayerNorm keeps its default init)
        self.apply(weights_init)

    def forward(self, state, action):
        xu = torch.cat([state, action], dim=1)      # sac.py에서 이미 tensor를 device로 보냄 -> CPU overhead 제거

        if self.use_ln:
            x1 = F.relu(self.ln1(self.linear1(xu)))
            x1 = F.relu(self.ln2(self.linear2(x1)))
            x1 = self.linear3(x1)

            x2 = F.relu(self.ln4(self.linear4(xu)))
            x2 = F.relu(self.ln5(self.linear5(x2)))
            x2 = self.linear6(x2)
        else:
            x1 = F.relu(self.linear1(xu))
            x1 = F.relu(self.linear2(x1))
            x1 = self.linear3(x1)

            x2 = F.relu(self.linear4(xu))
            x2 = F.relu(self.linear5(x2))
            x2 = self.linear6(x2)
        # this is actually two critic networks
        return x1, x2


class GaussianPolicy(FCActionPolicy):
    def __init__(self, args, action_space=None):
        super(GaussianPolicy, self).__init__()
        self.configure_fc_actions(args, action_space)
        input_dim = args.obs_dim
        num_actions = args.action_dim
        hidden_dim = 256
        self.min_log_std = -10.0
        self.max_log_std = 2.0
        
        self.linear1 = nn.Linear(input_dim, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, hidden_dim)

        self.mean_linear = nn.Linear(hidden_dim, num_actions)
        self.log_std_linear = nn.Linear(hidden_dim, num_actions)

        # optional LayerNorm on hidden layers (Linear -> LayerNorm -> ReLU)
        self.use_ln = bool(getattr(args, "actor_layernorm", False))
        if self.use_ln:
            self.ln1 = nn.LayerNorm(hidden_dim)
            self.ln2 = nn.LayerNorm(hidden_dim)

        self.apply(weights_init)
        
        # action rescaling
        if action_space is None:
            self.action_scale = torch.tensor(1.0)
            self.action_bias = torch.tensor(0.0)
        else:
            self.action_scale = torch.FloatTensor((action_space.high-action_space.low)/2.0)
            self.action_bias = torch.FloatTensor((action_space.high+action_space.low)/2.0)
    
    def forward(self, state):
        if self.use_ln:
            x = F.relu(self.ln1(self.linear1(state)))
            x = F.relu(self.ln2(self.linear2(x)))
        else:
            x = F.relu(self.linear1(state))
            x = F.relu(self.linear2(x))
        mean = self.mean_linear(x)
        log_std = self.log_std_linear(x)
        # Bound log-std to keep variance in a trainable range. -> nan_to_num 제거로 인한 GPU kernel 낭비 최소화
        log_std = torch.clamp(log_std, min=self.min_log_std, max=self.max_log_std)
        return mean, log_std
    
    def get_action(self, state):
        mean, log_std = self.forward(state)     # Tensor(1,1)
        std = log_std.exp()     # value section: exp([-10, 2]) --> [4e-5, 7.3891]
        normal = Normal(mean, std)
        # reparameterization trick, including noise
        x_t = normal.rsample()  # Gaussian dist에서 resampling，output：mean+std*sample
        # Enforcing Action Bound, a = tanh(u)
        y_t = torch.tanh(x_t)   # value section: [-1, 1]
        scale, bias = self.action_affine(state)
        action = y_t*scale+bias  # normalized, feasible dP/ramp when ramp > 0
        # log miu(u|s)
        log_us = normal.log_prob(x_t)       # x_t log prob
        # log pi(a|s), a = tanh(u) enforcing action bound, change of variable from u to a
        log_prob = log_us - torch.log(1.000001-y_t.pow(2)) - torch.log(scale)
        log_prob = log_prob.sum(1, keepdim=True)
        mean = torch.tanh(mean)*scale+bias
        return action, log_prob, mean

    def deterministic_action(self, state):
        """평가/배포 시 쓰는 결정론적 행동 (탐색 노이즈 없음)."""
        mean, _ = self.forward(state)
        scale, bias = self.action_affine(state)
        return torch.tanh(mean)*scale+bias

    def to(self, device):
        self.action_scale = self.action_scale.to(device)
        self.action_bias = self.action_bias.to(device)
        return super(GaussianPolicy, self).to(device)


class BetaPolicy(FCActionPolicy):
    """Beta 분포 정책 (Chou et al., ICML 2017).

    tanh-Gaussian 은 support 가 무한대인 분포를 유계 행동공간에 밀어넣기 때문에 경계
    근처에서 bias 가 생긴다. 특히 SAC 에서는 tanh 보정항 -log(1-y^2) 이 경계에서
    log pi 를 키우고, 엔트로피 항이 그것을 벌점하므로 **경계 행동(FC 완전 정지 /
    최대출력)이 구조적으로 억제**된다. Beta 는 [0,1] 유계 support 라 이 문제가 없다.

    Absolute-power mode maps x ~ Beta(alpha,beta) to a=2x-1.
    Fresh incremental policies map x to the state-dependent feasible dP/ramp
    interval instead. The returned action (not x) is used by replay and critics.
    """

    # x_t 가 정확히 0/1 이 되면 log_prob 이 발산하므로 그만큼만 잘라낸다.
    EPS = 1e-6

    def __init__(self, args, action_space=None):
        super(BetaPolicy, self).__init__()
        self.configure_fc_actions(args, action_space)
        input_dim = args.obs_dim
        num_actions = args.action_dim
        hidden_dim = 256

        self.linear1 = nn.Linear(input_dim, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, hidden_dim)

        self.alpha_linear = nn.Linear(hidden_dim, num_actions)
        self.beta_linear = nn.Linear(hidden_dim, num_actions)

        # optional LayerNorm on hidden layers (Linear -> LayerNorm -> ReLU)
        self.use_ln = bool(getattr(args, "actor_layernorm", False))
        if self.use_ln:
            self.ln1 = nn.LayerNorm(hidden_dim)
            self.ln2 = nn.LayerNorm(hidden_dim)

        self.apply(weights_init)

        # action rescaling: Beta 의 [0,1] -> 환경이 기대하는 [-1, 1]
        if action_space is None:
            self.action_scale = torch.tensor(2.0)
            self.action_bias = torch.tensor(-1.0)
        else:
            self.action_scale = torch.FloatTensor(action_space.high-action_space.low)
            self.action_bias = torch.FloatTensor(action_space.low)
        # a = x*scale + bias 의 야코비안 |da/dx| = scale. log pi(a) = log p(x) - log(scale)
        self.register_buffer("_log_scale", torch.log(torch.as_tensor(2.0)))

    def forward(self, state):
        if self.use_ln:
            x = F.relu(self.ln1(self.linear1(state)))
            x = F.relu(self.ln2(self.linear2(x)))
        else:
            x = F.relu(self.linear1(state))
            x = F.relu(self.linear2(x))
        # softplus + 1 -> alpha, beta >= 1 이라 단봉(unimodal) 이 보장된다.
        alpha = F.softplus(self.alpha_linear(x)) + 1.0
        beta = F.softplus(self.beta_linear(x)) + 1.0
        return alpha, beta

    def get_action(self, state):
        alpha, beta = self.forward(state)
        dist = Beta(alpha, beta)
        x_t = dist.rsample()                       # reparameterized, [0, 1]
        x_t = x_t.clamp(self.EPS, 1.0-self.EPS)    # log_prob 발산 방지
        scale, bias = self.action_affine(state, unit_interval=True)
        action = x_t*scale+bias
        # 스케일 야코비안 보정: tanh-Gaussian 과 log pi 스케일을 맞춰야
        # target_entropy 가 두 정책에서 같은 의미를 갖는다.
        log_prob = dist.log_prob(x_t) - torch.log(scale)
        log_prob = log_prob.sum(1, keepdim=True)
        mean = alpha/(alpha+beta)*scale+bias
        return action, log_prob, mean

    def deterministic_action(self, state):
        """평가/배포 시 쓰는 결정론적 행동 = 분포의 평균 alpha/(alpha+beta)."""
        alpha, beta = self.forward(state)
        scale, bias = self.action_affine(state, unit_interval=True)
        return alpha/(alpha+beta)*scale+bias

    def to(self, device):
        self.action_scale = self.action_scale.to(device)
        self.action_bias = self.action_bias.to(device)
        return super(BetaPolicy, self).to(device)

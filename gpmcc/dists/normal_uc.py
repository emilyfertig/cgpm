# -*- coding: utf-8 -*-

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from math import log

import numpy as np
import scipy

from gpmcc.dists.normal import Normal

LOG2 = log(2.0)
LOGPI = log(np.pi)
LOG2PI = log(2*np.pi)

class NormalUC(Normal):
    """Normal distribution with normal prior on mean and gamma prior on
    precision. Uncollapsed.

    rho ~ Gamma(nu/2, s/2)
    mu ~ Normal(m, rho)
    X ~ Normal(mu, r*rho)

    http://www.stats.ox.ac.uk/~teh/research/notes/GaussianInverseGamma.pdf
    Note that Teh uses Normal-InverseGamma to mean Normal-Gamma for prior.
    """

    def __init__(self, N=0, sum_x=0, sum_x_sq=0, mu=None, rho=None, m=0,
            r=1, s=1, nu=1, distargs=None):
        # Invoke parent.
        super(NormalUC, self).__init__(N=N, sum_x=sum_x, sum_x_sq=sum_x_sq,
            m=m, r=r, s=s, nu=nu, distargs=distargs)
        # Uncollapsed mean and precision parameters.
        self.mu, self.rho = mu, rho
        if mu is None or rho is None:
            self.transition_params()

    def predictive_logp(self, x):
        return NormalUC.calc_predictive_logp(x, self.mu, self.rho)

    def marginal_logp(self):
        data_logp = NormalUC.calc_log_likelihood(self.N, self.sum_x,
            self.sum_x_sq, self.rho, self.mu)
        prior_logp = NormalUC.calc_log_prior(self.mu, self.rho, self.m,
            self.r, self.s, self.nu)
        return data_logp + prior_logp

    def singleton_logp(self, x):
        return NormalUC.calc_predictive_logp(x, self.mu, self.rho)

    def simulate(self):
        return np.random.normal(self.mu, 1./self.rho**.5)

    def transition_params(self):
        rn, nun, mn, sn = NormalUC.posterior_hypers(self.N, self.sum_x,
            self.sum_x_sq, self. m, self.r, self.s, self.nu)
        self.mu, self.rho = NormalUC.sample_parameters(mn, rn, sn, nun)

    @staticmethod
    def name():
        return 'normal_uc'

    @staticmethod
    def is_collapsed():
        return False

    ##################
    # HELPER METHODS #
    ##################

    @staticmethod
    def calc_predictive_logp(x, mu, rho):
        return scipy.stats.norm.logpdf(x, loc=mu, scale=1./rho**.5)

    @staticmethod
    def calc_log_likelihood(N, sum_x, sum_x_sq, rho, mu):
        return -(N / 2.) * LOG2PI + (N / 2.) * log(rho) - \
            .5 * (rho * (N * mu * mu - 2 * mu * sum_x + sum_x_sq))

    @staticmethod
    def calc_log_prior(mu, rho, m, r, s, nu):
        """Distribution of parameters (mu rho) ~ NG(m, r, s, nu)"""
        log_rho = scipy.stats.gamma.logpdf(rho, nu/2., scale=2./s)
        log_mu = scipy.stats.norm.logpdf(mu, loc=m, scale=1./(r*rho)**.5)
        return log_mu + log_rho



import torch
import torch.nn as nn

from machina import loss_functional as lf
from machina.misc import logger


def train(traj,
        pol, targ_pol, qf, targ_qf,
        optim_pol, optim_qf,
        epoch, batch_size,# optimization hypers
        tau, gamma, lam # advantage estimation
        ):

    pol_losses = []
    qf_losses = []
    logger.log("Optimizing...")
    for batch in traj.random_batch(batch_size, epoch):
        qf_bellman_loss = lf.bellman(qf, targ_qf, targ_pol, batch, gamma)
        optim_qf.zero_grad()
        qf_bellman_loss.backward()
        optim_qf.step()

        pol_loss = lf.dpg(pol, qf, batch)
        optim_pol.zero_grad()
        pol_loss.backward()
        optim_pol.step()

        for p, targ_p in zip(pol.parameters(), targ_pol.parameters()):
            targ_p.detach().copy_((1 - tau) * targ_p.detach() + tau * p.detach())
        for q, targ_q in zip(qf.parameters(), targ_qf.parameters()):
            targ_q.detach().copy_((1 - tau) * targ_q.detach() + tau * q.detach())

        qf_losses.append(qf_bellman_loss.detach().cpu().numpy())
        pol_losses.append(pol_loss.detach().cpu().numpy())
    logger.log("Optimization finished!")

    return {'PolLoss': pol_losses, 'QfLoss': qf_losses}

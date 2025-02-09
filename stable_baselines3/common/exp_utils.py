import os
from types import FunctionType as function
from typing import Callable

import gym
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch as th
from matplotlib.colors import CSS4_COLORS, TABLEAU_COLORS
from scipy.spatial.distance import jensenshannon as jsd

from stable_baselines3.common.vec_env import DummyVecEnv, VecVideoRecorder


class DiscriminatorFunction:
    def __init__(self, f, name, output_size, env="", function_kwargs=None):
        self.env = env
        self.name = name
        self.f = f
        self.output_size = output_size
        self.function_kwargs = function_kwargs

    def __call__(self, obs):
        return self.f(obs, **self.function_kwargs)


def print_traj_nav_2d_static(
    model,
    n_skills,
    n_trajs=1,
    n_seeds=1,
    show_target=False,
    static=True,
    max_steps=100,
    manual_seeds=None,
    figsize=None,
    title="",
    xlabel="",
    ylabel="",
):
    if n_skills <= 10:
        colors = list(TABLEAU_COLORS.keys())
    else:
        colors = list(CSS4_COLORS.keys())

    if figsize is None:
        plt.figure(figsize=(12, 10))
    if manual_seeds is None:
        seeds = np.random.randint(1000, size=n_seeds)
    else:
        seeds = manual_seeds
    for seed in seeds:
        trajs = []
        for k in range(n_trajs):
            if n_skills == 1:
                traj = generate_trajectory(
                    model, 0, max_steps, return_actions=False, seed=int(seed)
                )
                plt.plot(*traj[:, :2].T, color=colors[k])

            else:

                for i in range(n_skills):
                    traj = generate_trajectory(
                        model, i, max_steps, return_actions=False, seed=int(seed)
                    )
                    plt.plot(*traj[:, :2].T, color=colors[i])

        if show_target:
            if static:
                plt.plot(*traj[0, 2:4].T, "ko")

    for i in range(n_skills):
        plt.plot(*[np.nan] * 2, label=f"skill {i}", color=colors[i])
    if show_target:
        plt.plot(*[np.nan] * 2, "ko", label="target")
    plt.xlim(-0.2, 0.6)
    plt.ylim(-0.2, 0.6)
    # plt.legend()
    plt.rcParams.update({"font.size": 22})
    plt.title(title, fontsize=50, weight=500)
    plt.xlabel(xlabel, fontsize=40, fontweight=2)
    plt.ylabel(ylabel, fontsize=40, fontweight=2)
    plt.show()


def print_traj_nav_2d(
    model,
    n_skills,
    n_trajs=1,
    n_seeds=1,
    show_target=False,
    static=False,
    max_steps=100,
    manual_seeds=None,
    figsize=None,
    title="",
    xlabel="",
    ylabel="",
):
    if n_skills <= 10:
        colors = list(TABLEAU_COLORS.keys())
    else:
        colors = list(CSS4_COLORS.keys())

    if figsize is None:
        plt.figure(figsize=(12, 10))
    if manual_seeds is None:
        seeds = np.random.randint(1000, size=n_seeds)
    else:
        seeds = manual_seeds
    for seed in seeds:
        trajs = []

        for k in range(n_trajs):
            if n_skills == 1:
                traj = generate_trajectory(
                    model, i, max_steps, return_actions=False, seed=int(seed)
                )
                plt.plot(*traj[:, :2].T, color=colors[k])

            else:

                for i in range(n_skills):
                    traj = generate_trajectory(
                        model, i, max_steps, return_actions=False, seed=int(seed)
                    )
                    plt.plot(*traj[:, :2].T, color=colors[i])

        if show_target:
            if static:
                plt.plot(*traj[0, 2:4].T, "ko")
            else:
                plt.plot(*traj[0, 2:4].T + traj[0, :2].T, "ko")

    for i in range(n_skills):
        plt.plot(*[np.nan] * 2, label=f"skill {i}", color=colors[i])
    if show_target:
        plt.plot(*[np.nan] * 2, "ko", label="target")
    plt.xlim(-1, 1)
    plt.ylim(-1, 1)
    # plt.legend()
    plt.rcParams.update({"font.size": 22})
    plt.title(title, fontsize=50, weight=500)
    plt.xlabel(xlabel, fontsize=40, fontweight=2)
    plt.ylabel(ylabel, fontsize=40, fontweight=2)
    plt.show()


def get_paths(
    env_id,
    n_skills,
    prior,
    train_freq,
    t_start,
    t_end,
    gradient_steps,
    buffer_size,
    disc_on,
    seed,
    ent_coef,
    combined_rewards,
    beta,
    smerl,
    eps,
    model_prefix="",
):
    train_freq_name = "".join([str(x)[:2] for x in train_freq])
    if isinstance(disc_on, DiscriminatorFunction):
        disc_on_name = disc_on.name
    else:
        disc_on_name = "".join([str(x) for x in disc_on])
        if len(disc_on_name) > 5:
            disc_on_name = disc_on_name[:3] + "..." + disc_on_name[-3:]
    if smerl:
        smerl_name = f"smerl-{smerl}__eps-{eps}"
    else:
        smerl_name = ""
    env_name = env_id.split(":")[-1].lower()
    run_name = f"{env_name}__skills-{n_skills}__disc-{disc_on_name}__tf-{train_freq_name}__gs-{gradient_steps}__bf-{float(buffer_size):.2}__ent-{ent_coef}__start-{t_start:.2}__end-{t_end:.2}__s-{seed}"
    if combined_rewards:
        run_name = f"{env_name}__skills-{n_skills}__disc-{disc_on_name}__tf-{train_freq_name}__gs-{gradient_steps}__bf-{float(buffer_size):.2}__{smerl_name}__ent-{ent_coef}__beta-{beta:.2}__start-{t_start:.2}__end-{t_end:.2}__s-{seed}"

    log_path = (
        "./logs/"
        + env_name
        + "/"
        + combined_rewards * "combined_rew/"
        + f"{n_skills}-skills/"
        + model_prefix
        + "__".join(run_name.split("__")[2:-3])
    )
    save_path = (
        "./models/"
        + env_name
        + "/"
        + combined_rewards * "combined_rew/"
        + f"{n_skills}-skills/"
        + model_prefix
        + run_name
    )
    video_path = (
        "./video/"
        + env_name
        + "/"
        + combined_rewards * "combined_rew/"
        + f"{n_skills}-skills/"
        + run_name
    )
    run_name = "__".join(run_name.split("__")[-3:])
    log_path = os.path.normpath(log_path)
    save_path = os.path.normpath(save_path)
    video_path = os.path.normpath(video_path)
    return log_path, run_name, save_path, video_path


def generate_trajectory(model, skill_idx, episode_length, seed=0, return_actions=True):
    states = []
    actions = []
    env = model.env
    skill = np.zeros(model.prior.event_shape)
    skill[skill_idx] = 1

    env.seed(seed)
    obs = env.reset()
    states.append(obs.flatten())
    for i in range(episode_length - 1):
        obs = np.concatenate([obs, skill[None, :]], axis=1)
        action, _ = model.predict(obs)

        actions.append(action.flatten())
        obs, _, done, _ = env.step(action)

        if done:
            break

        states.append(obs.flatten())

    states = np.reshape(states, (-1, *model.observation_space.shape))
    actions = np.reshape(actions, (-1, *model.action_space.shape))
    if return_actions:
        return states, actions
    else:
        return states


def compute_jsd(states_1, states_2, model, bins=50, states=True):
    if states:
        states_low = model.observation_space.low
        states_high = model.observation_space.high
    else:
        states_low = model.action_space.low
        states_high = model.action_space.high

    states_hist_1 = []
    states_hist_2 = []
    jsd_l = []
    for i in range(len(states_low)):
        state_low = states_low[i]
        state_high = states_high[i]
        hist, bin_edges = np.histogram(
            states_1.T[i], bins=bins, range=[state_low, state_high], density=True
        )
        states_hist_1.append(hist * np.diff(bin_edges))
        hist, bin_edges = np.histogram(
            states_2.T[i], bins=bins, range=[state_low, state_high], density=True
        )
        states_hist_2.append(hist * np.diff(bin_edges))
        jsd_l.append(jsd(states_hist_1[i], states_hist_2[i]))
    return jsd_l


def record_skills(env_id, model, directory, name_prefix="", video_length=400):

    env = DummyVecEnv([lambda: gym.make(env_id)])
    prior = model.prior
    k = 0
    for z in prior.enumerate_support():
        k += 1
        video_env = VecVideoRecorder(
            env,
            directory,
            record_video_trigger=lambda x: x == 0,
            video_length=video_length,
            name_prefix=f"skill-{k}-" + name_prefix,
        )

        obs = video_env.reset()
        for _ in range(video_length + 1):
            obs = np.concatenate([obs, z[None, :]], axis=1)
            action, next_state = model.predict(obs)
            obs, _, _, _ = video_env.step(action)
            # Save the video
        env.close()
        env = DummyVecEnv([lambda: gym.make(env_id)])
        video_env.close()
    env.close()


def evaluate_jsd_skills(model, n_skills, episode_length, seeds, bins=50):
    n_obs = model.observation_space.shape[0]
    n_act = model.action_space.shape[0]
    trajs = np.zeros((len(seeds), n_skills, episode_length, n_obs + n_act))
    for s, seed in enumerate(seeds):
        for i in range(n_skills):
            seed = int(seed)
            states_1, actions_1 = generate_trajectory(
                model,
                skill_idx=i,
                episode_length=episode_length,
                seed=seed,
                return_actions=True,
            )
            pad_scheme = [(0, episode_length - len(states_1)), (0, 0)]

            states_1 = np.pad(
                states_1.astype(float), pad_scheme, constant_values=np.nan
            )
            trajs[s, i, :, :n_obs] = states_1
            pad_scheme = [(0, episode_length - len(actions_1)), (0, 0)]
            actions_1 = np.pad(
                actions_1.astype(float), pad_scheme, constant_values=np.nan
            )
            trajs[s, i, :, n_obs:] = actions_1

    jsd_m = np.full((len(seeds), n_skills, n_skills, n_obs + n_act), np.nan)
    for s in range(len(seeds)):
        for i in range(n_skills):
            j = 0
            while j < i:
                jsd_m[s, i, j, :n_obs] = compute_jsd(
                    trajs[s, i, :, :n_obs],
                    trajs[s, j, :, :n_obs],
                    model,
                    bins=bins,
                    states=True,
                )
                jsd_m[s, i, j, n_obs:] = compute_jsd(
                    trajs[s, i, :, n_obs:],
                    trajs[s, j, :, n_obs:],
                    model,
                    bins=bins,
                    states=False,
                )
                j += 1
    jsd_m_states = jsd_m[:, :, :, :n_obs].mean(axis=-1).mean(axis=0)
    jsd_m_actions = jsd_m[:, :, :, n_obs:].mean(axis=-1).mean(axis=0)
    jsd_s_pd = pd.DataFrame(jsd_m_states.ravel(), columns=["jsd_s"]).dropna()
    jsd_a_pd = pd.DataFrame(jsd_m_actions.ravel(), columns=["jsd_a"]).dropna()
    jsd_pd = pd.concat([jsd_s_pd, jsd_a_pd], axis=1)
    return jsd_pd


def evaluate_jsd_separation(model, n_skills, episode_length, seeds, bins=50):
    n_obs = model.observation_space.shape[0]
    n_act = model.action_space.shape[0]
    trajs = np.zeros((len(seeds), episode_length, n_obs + n_act))
    skills = np.zeros(len(seeds,))
    for s, seed in enumerate(seeds):
        skill_idx = np.random.randint(0, n_skills)
        seed = int(seed)
        states_1, actions_1 = generate_trajectory(
            model,
            skill_idx=skill_idx,
            episode_length=episode_length,
            seed=seed,
            return_actions=True,
        )
        skills[s] = skill_idx
        pad_scheme = [(0, episode_length - len(states_1)), (0, 0)]
        states_1 = np.pad(states_1.astype(float), pad_scheme, constant_values=np.nan)
        trajs[s, :, :n_obs] = states_1
        pad_scheme = [(0, episode_length - len(actions_1)), (0, 0)]
        actions_1 = np.pad(actions_1.astype(float), pad_scheme, constant_values=np.nan)
        trajs[s, :, n_obs:] = actions_1
    jsd_m = np.full((len(seeds), len(seeds), n_obs + n_act, 2), np.nan)
    for i in range(len(seeds)):
        j = 0
        while j < i:
            jsd_m[i, j, :n_obs, 0] = compute_jsd(
                trajs[i, :, :n_obs], trajs[j, :, :n_obs], model, bins=bins, states=True
            )
            jsd_m[i, j, n_obs:, 0] = compute_jsd(
                trajs[i, :, n_obs:], trajs[j, :, n_obs:], model, bins=bins, states=False
            )

            if skills[i] == skills[j]:
                jsd_m[i, j, :, 1] = 1.0
            else:
                jsd_m[i, j, :, 1] = 0.0

            j += 1

    jsd_m_states = jsd_m[:, :, :n_obs, 0].mean(axis=-1)
    jsd_m_actions = jsd_m[:, :, n_obs:, 0].mean(axis=-1)
    jsd_m_label = jsd_m[:, :, :, 1].mean(axis=-1)
    jsd_label_pd = pd.DataFrame(jsd_m_label.ravel(), columns=["label"]).dropna()
    jsd_s_pd = pd.DataFrame(jsd_m_states.ravel(), columns=["jsd_s"]).dropna()
    jsd_a_pd = pd.DataFrame(jsd_m_actions.ravel(), columns=["jsd_a"]).dropna()
    jsd_pd = pd.concat([jsd_s_pd, jsd_a_pd, jsd_label_pd], axis=1)
    return jsd_pd


def evaluate_jsd_separation_mixed(model, n_skills, episode_length, seeds, bins=50):
    n_obs = model.observation_space.shape[0]
    n_act = model.action_space.shape[0]
    trajs = np.zeros((len(seeds), episode_length, n_obs + n_act))
    skills = np.zeros((len(seeds), 2))
    for s, seed in enumerate(seeds):
        p = np.random.random()
        seed = int(seed)
        if p < 0.5:
            skill_idx = np.random.choice(np.arange(n_skills), size=2, replace=False)
            states_1, actions_1 = generate_mixed_trajectory(
                model,
                skills_idx=skill_idx,
                episode_length=episode_length,
                seed=seed,
                return_actions=True,
            )
            skills[s] = skill_idx
        else:
            skill_idx = np.random.randint(0, n_skills)
            states_1, actions_1 = generate_trajectory(
                model,
                skill_idx=skill_idx,
                episode_length=episode_length,
                seed=seed,
                return_actions=True,
            )

            skills[s] = [skill_idx] * 2
        pad_scheme = [(0, episode_length - len(states_1)), (0, 0)]
        states_1 = np.pad(states_1.astype(float), pad_scheme, constant_values=np.nan)
        trajs[s, :, :n_obs] = states_1
        pad_scheme = [(0, episode_length - len(actions_1)), (0, 0)]
        actions_1 = np.pad(actions_1.astype(float), pad_scheme, constant_values=np.nan)
        trajs[s, :, n_obs:] = actions_1

    jsd_m = np.full((len(seeds), len(seeds), n_obs + n_act, 2), np.nan)
    for i in range(len(seeds)):
        j = 0
        while j < i:
            jsd_m[i, j, :n_obs, 0] = compute_jsd(
                trajs[i, :, :n_obs], trajs[j, :, :n_obs], model, bins=bins, states=True
            )
            jsd_m[i, j, n_obs:, 0] = compute_jsd(
                trajs[i, :, n_obs:], trajs[j, :, n_obs:], model, bins=bins, states=False
            )

            if (skills[i] == skills[j]).all():
                jsd_m[i, j, :, 1] = 4.0

            elif (np.sort(skills[i]) == np.sort(skills[j])).all():
                jsd_m[i, j, :, 1] = 1.0
            elif (np.sort(skills[i]) == np.sort(skills[j])).any():
                jsd_m[i, j, :, 1] = 2.0
            else:
                jsd_m[i, j, :, 1] = 0.0

            j += 1

    jsd_m_states = jsd_m[:, :, :n_obs, 0].mean(axis=-1)
    jsd_m_actions = jsd_m[:, :, n_obs:, 0].mean(axis=-1)
    jsd_m_label = jsd_m[:, :, :, 1].mean(axis=-1)
    jsd_label_pd = pd.DataFrame(jsd_m_label.ravel(), columns=["label"]).dropna()
    jsd_s_pd = pd.DataFrame(jsd_m_states.ravel(), columns=["jsd_s"]).dropna()
    jsd_a_pd = pd.DataFrame(jsd_m_actions.ravel(), columns=["jsd_a"]).dropna()
    jsd_pd = pd.concat([jsd_s_pd, jsd_a_pd, jsd_label_pd], axis=1)
    return jsd_pd


def generate_mixed_trajectory(
    model, skills_idx, episode_length, seed=0, return_actions=True
):
    states = []
    actions = []
    env = model.env

    env.seed(seed)
    obs = env.reset()
    states.append(obs.flatten())
    for i in range(episode_length - 1):
        if i < episode_length // 2:
            skill = th.zeros(model.prior.event_shape)
            skill[skills_idx[0]] = 1
        else:
            skill = th.zeros(model.prior.event_shape)
            skill[skills_idx[1]] = 1

        obs = np.concatenate([obs, skill[None, :]], axis=1)
        action, _ = model.predict(obs)

        actions.append(action.flatten())
        obs, _, done, _ = env.step(action)

        if done:
            break

        states.append(obs.flatten())

    states = np.reshape(states, (-1, *model.observation_space.shape))
    actions = np.reshape(actions, (-1, *model.action_space.shape))
    if return_actions:
        return states, actions
    else:
        return states


def linear_schedule(
    initial_value: float, final_value: float, end: float = 0
) -> Callable[[float], float]:
    """
    Linear learning rate schedule.

    :param initial_value: Initial learning rate.
    :param final_value: Final learning rate
    :param end: Progress remaining where final value will be reached.
    :return: schedule that computes
        current learning rate depending on remaining progress
    """
    assert 0 < end < 1

    def func(progress_remaining: float) -> float:
        """
        Progress will decrease from 1 (beginning) to 0.

        :param progress_remaining:
        :return: current learning rate
        """
        if progress_remaining < end:
            lr = final_value
        else:
            x0 = end
            x1 = 1
            y0 = final_value
            y1 = initial_value
            a = (y1 - y0) / (x1 - x0)
            b = y1 - a * x1

            lr = a * progress_remaining + b
        return lr

    return func


def multi_step_schedule(values, milestones):
    mlst = np.array(milestones)
    values = np.array(values)
    assert (mlst[::-1] == np.sort(mlst)).all()
    assert ((mlst < 1) & (mlst > 0)).all()

    def func(progress_remaining: float) -> float:
        if len(mlst[progress_remaining < mlst]) > 0:
            idx = np.argmin(mlst[progress_remaining < mlst])
        else:
            idx = -1
        return values[idx + 1]

    return func

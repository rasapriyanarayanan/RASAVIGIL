"""Quotes and messages. Escalating tone: calm -> firm -> strict -> final."""
from __future__ import annotations

import random

# (quote, author)
QUOTES = [
    ("It is not that we have a short time to live, but that we waste a lot of it.", "Seneca"),
    ("Lost time is never found again.", "Benjamin Franklin"),
    ("Concentrate all your thoughts upon the work at hand. The sun's rays do not burn until brought to a focus.", "Alexander Graham Bell"),
    ("Discipline is the bridge between goals and accomplishment.", "Jim Rohn"),
    ("Either you run the day, or the day runs you.", "Jim Rohn"),
    ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
    ("The key is not to prioritize what's on your schedule, but to schedule your priorities.", "Stephen Covey"),
    ("Amateurs sit and wait for inspiration; the rest of us just get up and go to work.", "Stephen King"),
    ("Lack of direction, not lack of time, is the problem.", "Zig Ziglar"),
    ("Focus on being productive instead of busy.", "Tim Ferriss"),
    ("You will never find time for anything. If you want time, you must make it.", "Charles Buxton"),
    ("What you do every day matters more than what you do once in a while.", "Gretchen Rubin"),
    ("Well begun is half done.", "Aristotle"),
    ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
    ("Your future is created by what you do today, not tomorrow.", "Robert Kiyosaki"),
]

# Messages per warning level. Level 1 is the first alert at the threshold.
WARNING_TITLES = {
    1: "DISTRACTION DETECTED",
    2: "I AM STILL WATCHING",
    3: "THIS IS YOUR FINAL WARNING",
    4: "ACCESS RESTRICTED",
}

WARNING_MESSAGES = {
    1: [
        "{minutes} minutes on {app}. Your goals did not take a break. Close it and return to your work.",
        "You have been drifting for {minutes} minutes on {app}. Consider this your first and politest warning.",
        "{app} has had {minutes} minutes of your life. That is enough. Back to work.",
    ],
    2: [
        "Warning ignored. {minutes} minutes lost on {app}. Every minute here is a minute your future self pays for.",
        "You looked at my warning and chose {app} anyway. {minutes} minutes gone. Do better.",
        "I do not get tired and I do not look away. {minutes} minutes on {app}. Close it now.",
    ],
    3: [
        "{minutes} minutes wasted on {app}. Excuses are not accepted here. Restrictions are now active.",
        "Final warning. {app} will be minimized for you if you do not leave. Choose your work.",
        "You were warned twice. {minutes} minutes on {app}. Discipline is a decision, make it now.",
    ],
    4: [
        "{app} has been restricted. You have lost {minutes} minutes. Return to your task and earn your freedom back.",
        "The owl has spoken: {app} is closed to you. {minutes} minutes were enough.",
    ],
}

LIMIT_MESSAGES = [
    "Daily distraction limit of {limit} minutes reached. {app} is locked for the rest of today.",
    "You have spent your entire distraction budget for today ({limit} minutes). The owl closes {app}.",
]

# Shown after the user comes back to work following a warning.
RECOVERY_MESSAGES = [
    "Welcome back. You lost {minutes} minutes on {app}. Now make the next ones count.",
    "Good. Focus restored after {minutes} minutes of distraction. Do not let it happen twice.",
    "{minutes} minutes are gone for good. The next {minutes} can still be useful. Continue.",
    "Back to work, as it should be. The owl is satisfied, for now.",
]

SNOOZE_MESSAGES = [
    "Snooze granted for {minutes} minutes. Use it wisely, I will be back.",
]

NO_SNOOZE_MESSAGE = "No snoozes left today. Discipline does not negotiate."

# Daily report verdicts by focus score (percent). First match with score >= threshold wins.
VERDICTS = [
    (85, "Outstanding discipline. The owl bows its head.", "Excellence is not an act but a habit."),
    (70, "Solid focus. A few slips, nothing you cannot fix.", "Small disciplines repeated daily lead to great achievements."),
    (50, "Average. You can do much better than average.", "Do what you can, with what you have, where you are."),
    (30, "Distractions won today. Tomorrow you take it back.", "Failure is not fatal, but failure to change might be."),
    (0, "A day lost to scrolling. The owl is disappointed.", "Tomorrow is the first blank page of a 365-page book. Write a good one."),
]


def random_quote() -> tuple[str, str]:
    return random.choice(QUOTES)


def warning_title(level: int) -> str:
    return WARNING_TITLES[min(level, max(WARNING_TITLES))]


def warning_message(level: int, app: str, minutes: int) -> str:
    pool = WARNING_MESSAGES[min(level, max(WARNING_MESSAGES))]
    return random.choice(pool).format(app=app, minutes=minutes)


def limit_message(app: str, limit: int) -> str:
    return random.choice(LIMIT_MESSAGES).format(app=app, limit=limit)


def recovery_message(app: str, minutes: int) -> str:
    return random.choice(RECOVERY_MESSAGES).format(app=app, minutes=minutes)


def verdict(score: float) -> tuple[str, str]:
    for threshold, text, quote in VERDICTS:
        if score >= threshold:
            return text, quote
    return VERDICTS[-1][1], VERDICTS[-1][2]

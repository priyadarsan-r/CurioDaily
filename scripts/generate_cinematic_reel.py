"""
CLI Application: Convert any 1-minute narration script into a high-retention cinematic vertical video.
Usage:
    python scripts/generate_cinematic_reel.py --title "The Richat Structure" --category daily_mystery --sample
    python scripts/generate_cinematic_reel.py --script-file script.txt --title "The Framing Effect" --category human_psychology
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from media.cinematic_engine import CinematicVideoGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CinematicVideoCLI")

SAMPLE_SCRIPTS = {
    "daily_mystery": (
        "When astronauts first orbited Earth in the 1960s, they peered down at the desolate sands of Mauritania—"
        "and saw a giant, terrifying eye staring back at them. A perfect bullseye, twenty-five miles wide, carved "
        "into the desert floor. For decades, scientists insisted it had to be the impact crater of a colossal prehistoric asteroid. "
        "Except... when geologists finally reached the remote heart of the Sahara, they found zero impact shocked quartz. "
        "The truth was even more astonishing: a gigantic dome of molten magma swelled beneath the Earth's crust a hundred million years ago, "
        "then slowly collapsed—leaving behind concentric rings of ancient quartzite eroded over aeons. "
        "It is so massive, astronauts on the International Space Station still use it as a visual landmark today. "
        "Our planet is covered in wonders hidden in plain sight. What else are we missing?"
    ),
    "money_secrets": (
        "Imagine two people saving the exact same amount of money. One retires twenty years earlier than the other. "
        "How? It comes down to a deceptively simple mental shortcut called the Rule of 72. "
        "Most of us are conditioned to think in straight lines. We save a dollar, we earn a dollar. "
        "But wealth doesn’t grow linearly—it curves exponentially. Here is the math: take the number 72 and divide it by your expected rate of return. "
        "That single calculation tells you exactly how many years it takes for your capital to double. "
        "At nine percent return, your money doubles every eight years. At four percent? It takes eighteen. "
        "A mere five percent difference isn't just extra profit—it’s an entire lifetime of compound freedom. "
        "The moment you stop measuring your finances in dollars and start measuring them in doubling cycles... the entire game changes. "
        "The real question isn't whether your money will compound—it’s who it will compound for."
    ),
    "human_psychology": (
        "If a doctor told you a medical procedure had a ninety percent survival rate, would you take it? "
        "What if they told you it had a ten percent mortality rate? Exactly. "
        "Logically, both statements are identical. But emotionally? Your brain treats them as two completely different universes. "
        "This is the Framing Effect. Decades of cognitive science reveal a hidden vulnerability in human nature: "
        "our minds are terrified of loss, but remarkably indifferent to equivalent gains. "
        "Marketers, politicians, and even the choices on a restaurant menu exploit this subtle bias every single day—"
        "simply by choosing which side of the coin to show you. "
        "The moment you recognize that the frame is an illusion, you take back control over your decisions. "
        "Next time you face a major choice, flip the question upside down. You might be shocked at what you see."
    ),
    "future_is_here": (
        "Every smartphone in our pockets and every electric car on the road shares the same dirty secret: liquid electrolyte batteries. "
        "They degrade, they overheat, and under pressure—they can ignite. For twenty years, clean energy was trapped behind a stubborn chemistry wall. "
        "Until now. Enter solid-state technology. By replacing flammable liquids with ultra-dense ceramic electrolytes, engineers have unlocked something extraordinary: "
        "double the energy density, eight-minute fast charging, and virtually zero fire risk. "
        "It is the missing piece for electric aviation and thousand-mile vehicles. We aren't just looking at a better battery. "
        "We are watching the permanent obsolescence of fossil fuels in real time. "
        "The next industrial revolution isn't coming in fifty years. It’s sitting in laboratories right now."
    ),
}


def main():
    parser = argparse.ArgumentParser(description="CurioDaily AI Cinematic Video Generator")
    parser.add_argument("--script", type=str, default=None, help="Raw 1-minute narration script text")
    parser.add_argument("--script-file", type=str, default=None, help="Path to text file containing narration script")
    parser.add_argument("--title", type=str, default=None, help="Title of the documentary reel")
    parser.add_argument("--category", type=str, default="daily_mystery", choices=["daily_mystery", "money_secrets", "human_psychology", "future_is_here"])
    parser.add_argument("--content-id", type=str, default=None, help="Custom content ID for output directory")
    parser.add_argument("--sample", action="store_true", help="Generate a showcase video using built-in high-retention script")
    args = parser.parse_args()

    category = args.category
    title = args.title

    if args.sample or (not args.script and not args.script_file):
        script = SAMPLE_SCRIPTS.get(category, SAMPLE_SCRIPTS["daily_mystery"])
        title = title or {
            "daily_mystery": "The Richat Structure: The Eye of the Sahara",
            "money_secrets": "The Rule of 72: Exponential Freedom",
            "human_psychology": "The Framing Effect: Subconscious Bias",
            "future_is_here": "Solid-State Batteries: The Clean Revolution",
        }.get(category, "CurioDaily Cinematic Mystery")
        logger.info(f"Using curated TED-talk retention script for: {title}")
    elif args.script_file:
        script = Path(args.script_file).read_text(encoding="utf-8").strip()
        title = title or Path(args.script_file).stem.replace("_", " ").title()
    else:
        script = args.script
        title = title or "CurioDaily Documentary"

    cid = args.content_id or f"cinematic_{category[:4]}_{abs(hash(title)) % 100000:05d}"

    generator = CinematicVideoGenerator()
    result = generator.generate_cinematic_reel(
        script=script,
        title=title,
        category=category,
        content_id=cid
    )

    print("\n" + "=" * 60)
    print("🎬 CURIODAILY CINEMATIC REEL GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Title:         {result['title']}")
    print(f"Category:      {result['category']}")
    print(f"Scene Count:   {result['scene_count']} cuts (high-velocity visual pacing)")
    print(f"Duration:      {result['duration_sec']:.2f} seconds")
    print(f"Quality Check: {result['quality_status']} (Passed: {result['quality_passed']})")
    print(f"Video Output:  {result['video_path']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

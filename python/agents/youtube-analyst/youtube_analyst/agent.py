import os
import pathlib

from google import genai
from google.adk.agents import Agent
from google.adk.skills import load_skill_from_dir
from google.adk.tools import load_artifacts
from google.adk.tools.skill_toolset import SkillToolset

from .common.llm import GeminiWithLocation
from .common.utils import load_prompt
from .config import config
from .tools import (
    aggregate_comment_sentiment,
    analyze_sentiment_heuristic,
    calculate_engagement_metrics,
    calculate_match_score,
    generate_timestamp_url,
    get_channel_details,
    get_comment_replies,
    get_current_date_time,
    get_date_range,
    get_trending_videos,
    get_video_comments,
    get_video_details,
    get_video_transcript,
    publish_file,
    render_html,
    search_channel_videos,
    search_youtube,
    submit_feedback,
)
from .visualization_agent import visualization_agent

# ---------------------------------------------------------------------------
# ADK Skills: Modular, progressive disclosure workflows
# ---------------------------------------------------------------------------
skills_root = pathlib.Path(__file__).parent / "skills"

skills = [
    load_skill_from_dir(skills_root / name)
    for name in [
        "abcd-framework-audit",
        "creative-insight-analyzer",
        "daily-briefing",
        "debate-synthesizer",
        "deep-exploration",
        "industry-landscape-briefing",
        "kol-discovery",
        "multi-video-synthesis",
        "poi-discovery-briefing",
        "product-launch-audit",
        "sentiment-analysis",
        "visualization-reporting",
    ]
]

skill_toolset = SkillToolset(skills=skills)

youtube_agent = Agent(
    model=GeminiWithLocation(
        model=config.agent_settings.model, location=config.GOOGLE_GENAI_LOCATION
    ),
    name="youtube_agent",
    description="Agent for YouTube analysis and data retrieval",
    instruction=load_prompt(os.path.dirname(__file__), "youtube_agent.txt"),
    sub_agents=[visualization_agent],
    tools=[
        search_youtube,
        get_trending_videos,
        get_video_details,
        get_channel_details,
        search_channel_videos,
        get_video_comments,
        get_comment_replies,
        aggregate_comment_sentiment,
        get_video_transcript,
        generate_timestamp_url,
        calculate_engagement_metrics,
        calculate_match_score,
        analyze_sentiment_heuristic,
        get_current_date_time,
        get_date_range,
        submit_feedback,
        render_html,
        publish_file,
        skill_toolset,  # Registers list_skills, load_skill, load_skill_resource
        load_artifacts,
    ],
    generate_content_config=genai.types.GenerateContentConfig(
        max_output_tokens=config.YOUTUBE_AGENT_MAX_OUTPUT_TOKENS,
    ),
)

root_agent = youtube_agent

from dagster import job, op, Definitions, define_asset_job, AssetSelection
from extract.tweetloader import TweetExtractor
import os
from dotenv import load_dotenv

load_dotenv()

@op
def extract_tweets(context):
    """Extract tweets and perform sentiment analysis."""
    extractor = TweetExtractor()
    search_query = os.getenv(TWITTER_SEARCH_QUERY, 'data engineering')
    extractor.search_tweets(search_query)
    context.log.info(f"Completed tweet extraction for query: {search_query}")

@op
def transform_pinot_data(context):
    """Transform data in Apache Pinot."""
  
    transform_query = """
    SELECT 
        sentiment,
        COUNT(*) as tweet_count,
        DISTINCTCOUNT(id) as unique_tweets,
        AVG(public_metrics.retweet_count) as avg_retweets,
    FROM twitter_sentiment
    GROUP BY sentiment
    """
    # Execute your transformation using Pinot client
    context.log.info("Completed Pinot transformations")

# Define the job
@job
def twitter_sentiment_pipeline():
    transform_pinot_data(extract_tweets())

# Create Dagster definitions
defs = Definitions(
    jobs=[twitter_sentiment_pipeline]
)

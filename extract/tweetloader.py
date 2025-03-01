import os
import tweepy
import json
import time
from openai import OpenAI
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from dotenv import load_dotenv

load_dotenv()

class TweetExtractor:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            wait_on_rate_limit=True
        )
        
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Try to connect to Kafka with retries
        retries = 5
        while retries > 0:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                    value_serializer=lambda x: json.dumps(x).encode('utf-8')
                )
                print("Successfully connected to Kafka")
                break
            except NoBrokersAvailable:
                print(f"Waiting for Kafka to be ready... {retries} retries left")
                retries -= 1
                time.sleep(10)
        
        if retries == 0:
            raise Exception("Failed to connect to Kafka after multiple retries")

    def search_tweets(self, query, max_results=100):
        """Search for tweets and return them with sentiment analysis."""
        print(f"Searching for tweets with query: {query}")
        tweets = self.client.search_recent_tweets(
            query=query,
            max_results=max_results,
            tweet_fields=['created_at', 'lang', 'public_metrics']
        )
        
        for tweet in tweets.data or []:
            sentiment = self._analyze_sentiment(tweet.text)
            
            tweet_data = {
                'id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at.isoformat(),
                'lang': tweet.lang,
                'public_metrics': tweet.public_metrics,
                'sentiment': sentiment
            }
            
            print(f"Processing tweet {tweet.id} with sentiment: {sentiment}")
            self._send_to_kafka(tweet_data)
            
    def _analyze_sentiment(self, text):
        """Analyze sentiment using OpenAI."""
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analyzer. Respond with only: POSITIVE, NEGATIVE, or NEUTRAL"},
                {"role": "user", "content": f"Analyze the sentiment of this tweet: {text}"}
            ],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    
    def _send_to_kafka(self, tweet_data):
        """Send tweet data to Kafka topic."""
        self.producer.send('twitter_sentiment', tweet_data)
        self.producer.flush()

if __name__ == "__main__":
    print("Starting Tweet Extractor...")
    extractor = TweetExtractor()
    query = os.getenv('TWITTER_SEARCH_QUERY', 'technology')
    print(f"Using search query: {query}")
    extractor.search_tweets(query)
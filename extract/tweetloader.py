import os

import json
import time
from openai import OpenAI
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from dotenv import load_dotenv

load_dotenv()
TWITTER_BASE_URL = "https://api.twitter.com/2"
class TweetExtractor:
    def __init__(self):
   
        
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

    def search_tweets(self, query, max_results=10):
        """Search for tweets and return them with sentiment analysis."""
        print(f"Searching for tweets with query: {query}")
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'lang', 'public_metrics']
            )
            
            if not tweets.data:
                print("No tweets found for the query")
                return
            
            print(f"Found {len(tweets.data)} tweets")
            for tweet in tweets.data:
                try:
                    sentiment = self._analyze_sentiment(tweet.text)
                    
                    tweet_data = {
                        'id': str(tweet.id),
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'lang': tweet.lang,
                        'public_metrics': tweet.public_metrics,
                        'sentiment': sentiment
                    }
                    
                    print(f"Processing tweet {tweet.id} with sentiment: {sentiment}")
                    self._send_to_kafka(tweet_data)
                except Exception as e:
                    print(f"Error processing tweet {tweet.id}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Error searching tweets: {str(e)}")
            
    def _analyze_sentiment(self, text):
        """Analyze sentiment using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a sentiment analyzer. Respond with only: POSITIVE, NEGATIVE, or NEUTRAL"},
                    {"role": "user", "content": f"Analyze the sentiment of this tweet: {text}"}
                ],
                max_tokens=10
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            return "NEUTRAL"  # Default to neutral on error
    
    def _send_to_kafka(self, tweet_data):
        """Send tweet data to Kafka topic."""
        try:
            self.producer.send('twitter_sentiment', tweet_data)
            self.producer.flush()
            print(f"Successfully sent tweet {tweet_data['id']} to Kafka")
        except Exception as e:
            print(f"Error sending to Kafka: {str(e)}")

if __name__ == "__main__":
    while True:
        try:
            print("Starting Tweet Extractor...")
            extractor = TweetExtractor()
            query = os.getenv('TWITTER_SEARCH_QUERY', 'technology')
            print(f"Using search query: {query}")
            extractor.search_tweets(query)
            print("Waiting 60 seconds before next batch...")
            time.sleep(60)  # Wait a minute before fetching more tweets
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying
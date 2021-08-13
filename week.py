import requests
import pandas as pd
import json
import ast
import yaml

# Before you can connect the Twitter API, 
# you’ll need to set up the URL to ensure it has the right fields so you get the right data back. 
def create_twitter_url(handle):
    max_results = 100
    mrf = "max_results={}".format(max_results)
    q = "query=from:{}".format(handle)
    url = "https://api.twitter.com/labs/2/tweets/search?tweet.fields=lang&{}&{}".format(mrf, q)
    return url

# To access the configuration file you created while setting up config.yaml
def process_yaml():
    with open("config.yaml") as file:
        return yaml.safe_load(file)

# To access the bearer token from your config.yaml file
def create_bearer_token(data):
    return data["search_tweets_v2"]["bearer_token"]


# To format the headers to pass in your bearer_token and url
def twitter_auth_and_connect(bearer_token, url):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    response = requests.request("GET", url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

def no_tweets(res_json):
    if res_json == {"meta": {"result_count": 0}}:
        print("The Twitter handle entered hasn't Tweeted in 7 days.")


def connect_to_azure(data):
    azure_url = "https://senti-on-tweet.cognitiveservices.azure.com/"
    sentiment_url = "{}text/analytics/v2.1/sentiment".format(azure_url)
    subscription_key = data["azure"]["subscription_key"]
    return sentiment_url, subscription_key


def azure_header(subscription_key):
    return {"Ocp-Apim-Subscription-Key": subscription_key}


def create_document_format(res_json):
    data_only = res_json["data"]
    doc_start = '"documents": {}'.format(data_only)
    str_json = "{" + doc_start + "}"
    dump_doc = json.dumps(str_json)
    doc = json.loads(dump_doc)
    return ast.literal_eval(doc)


def sentiment_scores(headers, sentiment_url, document_format):
    response = requests.post(sentiment_url, headers=headers, json=document_format)
    return response.json()


def mean_score(sentiments):
    sentiment_df = pd.DataFrame(sentiments["documents"])
    return sentiment_df["score"].mean()


def week_logic(week_score):
    if week_score > 0.75 or week_score == 0.75:
        print("This account had a positve week")
    elif week_score > 0.45 or week_score == 0.45:
        print("This account had a neautral week")
    else:
        print("This account had a negative week, I hope it gets better")


def main():
    handle = input("Enter the company's twitter username")
    url = create_twitter_url(handle)
    data = process_yaml()
    bearer_token = create_bearer_token(data)
    res_json = twitter_auth_and_connect(bearer_token, url)
    no_tweets(res_json)
    sentiment_url, subscription_key = connect_to_azure(data)
    headers = azure_header(subscription_key)
    document_format = create_document_format(res_json)
    sentiments = sentiment_scores(headers, sentiment_url, document_format)
    week_score = mean_score(sentiments)
    print(week_score)
    week_logic(week_score)


if __name__ == "__main__":
    main()

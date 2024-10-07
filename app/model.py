import boto3
from botocore.exceptions import ClientError
from vectSearch import generate_promt


client = boto3.client("bedrock-runtime", region_name='us-east-1')
model_id = "amazon.titan-text-premier-v1:0"


def ask(promt, settings):
    promt = generate_promt(promt)

    conversation = [
        {
            "role": "user",
            "content": [{"text": promt}],
        }
    ]

    try:
        response = client.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={"maxTokens": 1024, "stopSequences": [], "temperature": settings["temperature"], "topP": settings["top_p"]},
            additionalModelRequestFields={}
        )

        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text

    except (ClientError, Exception) as e:
        return f"Some errors with server. Try later..."

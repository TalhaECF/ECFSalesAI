

class CommonUtils:

    def __init__(self, client):
        pass

    @staticmethod
    def gpt_response(client, prompt):
        response =client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=10000,
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()
        return result

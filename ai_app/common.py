import re
import requests
import openai

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

    @staticmethod
    def gpt_response_json(client, prompt):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=10000,
            messages=[{"role": "user", "content": prompt}],
            response_format = {"type": "json_object"}
        )
        result = response.choices[0].message.content.strip()
        return result

    @staticmethod
    def load_prompt_without_remarks(questionnaire_content, copilot_response):
        """Loads the prompt from a file and injects dynamic questionnaire content."""
        file_path = "prompts/wbs_without_remarks.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            prompt_template = file.read()

        # Inject the questionnaire_content dynamically
        formatted_prompt = prompt_template.format(questionnaire_content=questionnaire_content,
                                                  copilot_response=copilot_response)

        return formatted_prompt

    @staticmethod
    def load_prompt_with_remarks(user_remarks, copilot_response, questionnaire_content, wbs_content):
        """Loads the prompt from a file and injects dynamic questionnaire content."""
        file_path = "prompts/wbs_with_remarks.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            prompt_template = file.read()

        # Inject the questionnaire_content dynamically
        formatted_prompt = prompt_template.format(user_remarks=user_remarks,
                                                  questionnaire_content=questionnaire_content, wbs_content=wbs_content,
                                                  copilot_response=copilot_response)

        return formatted_prompt



def gpt_response(client, prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10000,
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content.strip()
    return result


def summarize_text_with_gpt(client, text):
    """
    Summarizes the provided text using the new gpt_response method,
    preserving key details.
    """
    prompt = f"Please summarize the following text while preserving key details:\n\n{text}"
    try:
        summary = gpt_response(client, prompt)
        return summary
    except Exception as e:
        return f"Error during summarization: {str(e)}"


def get_summaries_from_text(client, input_text):
    """
    Extracts URLs from the provided input_text, browses each URL to retrieve content,
    summarizes each content using GPT (via gpt_response), and appends all summaries into one text variable.

    :param client: GPT client to be used for summarization.
    :param input_text: A string containing one or more URLs.
    :return: A string that contains the combined summaries of all URLs.
    """
    # Regex pattern to extract URLs
    urls = re.findall(r'(https?://\S+)', input_text)
    final_summary = ""

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                summary = summarize_text_with_gpt(client, content)
                final_summary += f"Summary for {url}:\n{summary}\n\n"
            # else:
            #     final_summary += f"Could not retrieve content from {url}. HTTP status code: {response.status_code}\n\n"
        except Exception as e:
            final_summary += f"Error retrieving content from {url}: {str(e)}\n\n"

    return final_summary

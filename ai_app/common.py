

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
    def load_prompt_without_remarks(questionnaire_content):
        """Loads the prompt from a file and injects dynamic questionnaire content."""
        file_path = "prompts/wbs_without_remarks.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            prompt_template = file.read()

        # Inject the questionnaire_content dynamically
        formatted_prompt = prompt_template.format(questionnaire_content=questionnaire_content)

        return formatted_prompt

    @staticmethod
    def load_prompt_with_remarks(user_remarks, questionnaire_content, wbs_content):
        """Loads the prompt from a file and injects dynamic questionnaire content."""
        file_path = "prompts/wbs_with_remarks.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            prompt_template = file.read()

        # Inject the questionnaire_content dynamically
        formatted_prompt = prompt_template.format(user_remarks=user_remarks,
                                                  questionnaire_content=questionnaire_content, wbs_content=wbs_content)

        return formatted_prompt
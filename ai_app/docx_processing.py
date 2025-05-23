import re
import os
from docx import Document
from lxml import etree
from typing import Dict, List

from decouple import config
from openai import AzureOpenAI

from .common import CommonUtils
from .utils import get_initial_form_by_search, get_discovery_questionnaire
from .wbs_utils import get_wbs_content

# Initialize OpenAI client
client = AzureOpenAI(
    api_key=config("OPENAI_API_KEY"),
    api_version=config("OPENAI_API_VERSION"),
    azure_endpoint = config("OPENAI_API_BASE"),
    azure_deployment=config("DEPLOYMENT_NAME"),
    )


def load_document(path: str) -> Document:
    """Load a Word document from the specified path."""
    try:
        return Document(path)
    except Exception as e:
        raise FileNotFoundError(f"Unable to load document: {e}")

def extract_content_control_texts(doc: Document) -> List[str]:
    """
    Extract text from all content controls (Structured Document Tags) in the document.
    """
    root = doc._element  # lxml element for <w:document>
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

    # Convert the root to an ElementTree
    tree = etree.ElementTree(root)

    # Find all content control elements in the document
    sdt_elements = tree.xpath('.//w:sdt', namespaces=ns)

    texts = []
    for sdt in sdt_elements:
        # Extract inner text content (if any text nodes exist in the content)
        content_elem = sdt.find('.//w:sdtContent', namespaces=ns)
        text = "".join(content_elem.itertext()) if content_elem is not None else ""
        texts.append(text)
    return texts


# def extract_placeholders(texts: List[str]) -> List[str]:
#     """
#     Extract all unique placeholders in the format [PLACEHOLDER] from a list of texts.
#     """
#     pattern = re.compile(r'\[([^\[\]]+)\]')
#     placeholders = set()
#     for text in texts:
#         matches = pattern.findall(text)
#         for match in matches:
#             placeholders.add(match.strip())
#     return list(placeholders)

def extract_placeholders(texts: List[str]) -> List[str]:
    """
    Extract both bracketed [PLACEHOLDER] and unbracketed Placeholder values
    from content control text blocks.
    """
    bracket_pattern = re.compile(r'\[([^\[\]]+)\]')
    plain_pattern = re.compile(r'\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\b')

    placeholders = set()

    for text in texts:
        # Bracketed placeholders
        bracket_matches = bracket_pattern.findall(text)
        placeholders.update(match.strip() for match in bracket_matches)

        # Plain title-case placeholders (e.g. Service Owner)
        plain_matches = plain_pattern.findall(text)
        for match in plain_matches:
            # Ignore common English words or already bracketed ones
            if match not in placeholders and not re.search(r'\[.*' + re.escape(match) + r'.*\]', text):
                placeholders.add(match.strip())

    return list(placeholders)





def generate_placeholder_dict(placeholders: List[str]) -> Dict[str, str]:
    """
    Generate a dictionary with placeholders as keys and empty strings as values.
    """
    return {placeholder: "" for placeholder in placeholders}

def replace_placeholders_in_content_controls(doc: Document, replacements: Dict[str, str]) -> None:
    """
    Replace placeholders in all content controls (including headers) with dummy values.
    """
    def process_element_tree(root_element):
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        tree = etree.ElementTree(root_element)
        sdt_elements = tree.xpath('.//w:sdt', namespaces=ns)

        for sdt in sdt_elements:
            content_elem = sdt.find('.//w:sdtContent', namespaces=ns)
            if content_elem is not None:
                for elem in content_elem.iter():
                    if elem.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t':
                        text = elem.text
                        if text:
                            for key, val in replacements.items():
                                placeholder = f'[{key}]'
                                if placeholder in text:
                                    text = text.replace(placeholder, val)
                            elem.text = text

    # Process main document body
    process_element_tree(doc._element)

    # Process headers
    for section in doc.sections:
        header = section.header
        if header is not None:
            process_element_tree(header._element)


def generate_openai_response(placeholders, access_token, project_id, initial_form_item_id, wbs_item_id):
    """
    Generate dummy values for each placeholder.
    For example, ${NAME} -> Dummy_NAME
    """
    initial_form_response = get_initial_form_by_search(access_token, initial_form_item_id, client)
    questionnaire_content = get_discovery_questionnaire(access_token, project_id)
    copilot_response = None

    file_path = os.path.join(os.path.dirname(__file__), '..', 'copilot_response.txt')
    file_path = os.path.abspath(file_path)

    with open(file_path, "r") as f:
        copilot_response = f.read()
        f.close()

    wbs_phases_content = get_wbs_content(access_token, wbs_item_id)

    prompt = f"""
        Here is a list of placeholders/keys: {placeholders}\n
        Return a JSON with these placeholders as keys and fill in the appropriate values using the context below:
        
        Initial Form Response: {initial_form_response}\n
        Filled Discovery Questionnaire: {questionnaire_content}\n
        Copilot Response: {copilot_response}\n
        WBS 4 Phases Content: {str(wbs_phases_content)}
        
        Instructions:
        - For Workload, only add add 2 phrase word
    """
    response_dict = eval(CommonUtils.gpt_response_json(client, prompt))
    response_dict = {key: str(val) for key,val in response_dict.items()}
    return response_dict


def process_document(input_path, output_path, access_token, project_id, initial_form_item_id, wbs_item_id):
    """
    Process the document: load, extract placeholders, generate dummy values,
    replace placeholders, and save the new document.
    """
    doc = load_document(input_path)
    texts = extract_content_control_texts(doc)
    placeholders = extract_placeholders(texts)
    replacements = generate_openai_response(placeholders, access_token, project_id, initial_form_item_id, wbs_item_id)
    # replacements = {placeholder: f"{placeholder}_dummy" for placeholder in placeholders}
    print(f"Here are the placeholders (key and values): {replacements}")
    replace_placeholders_in_content_controls(doc, replacements)
    doc.save(output_path)

# if __name__ == "__main__":
#     input_file = "template.docx"  # Replace with your input file path
#     output_file = "output.docx"   # Replace with your desired output file path
#     process_document(input_file, output_file)
#     print(f"Processed document saved as '{output_file}'.")

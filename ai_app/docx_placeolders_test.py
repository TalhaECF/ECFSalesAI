import zipfile
import xml.etree.ElementTree as ET

# Define the XML namespace for Word documents
WORD_NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Path to the .docx file (replace with the actual path if needed)
docx_path = "Naveen Ganeshe_InitialQuestinnaire.docx"

# Open the .docx file as a ZIP archive and read the document.xml content
with zipfile.ZipFile(docx_path) as docx_zip:
    xml_content = docx_zip.read('word/document.xml')

# Parse the XML content
root = ET.fromstring(xml_content)

# Find all paragraph elements in the document
paragraphs = root.findall('.//w:p', WORD_NS)

qa_dict = {}                  # Dictionary to hold question: answer pairs
current_question = None       # Track the current question text (without "Q:")
answer_lines = []             # Collect lines of the current answer

for para in paragraphs:
    # Extract all text from the paragraph (including runs and content controls)
    text = "".join(node.text for node in para.findall('.//w:t', WORD_NS) if node.text)
    text = text.strip()  # remove leading/trailing whitespace

    if text.startswith("Q:"):
        # Paragraph is a Question
        # If we were in the middle of collecting an answer for the previous question, save it first
        if current_question is not None:
            # Join collected answer lines (if multiple lines) into one string
            full_answer = "\n".join(answer_lines).strip()
            qa_dict[current_question] = full_answer
        # Start a new question (omit the "Q:" prefix for the dictionary key)
        current_question = text[len("Q:"):].strip()
        answer_lines = []  # reset answer collection for the new question

    elif text.startswith("A:"):
        # Paragraph is an Answer (or the beginning of an answer)
        # Remove the "A:" prefix and strip whitespace
        answer_text = text[len("A:"):].strip()
        if current_question:
            answer_lines.append(answer_text)

    else:
        # Paragraph is neither a new question nor a direct "A:" answer line.
        # If it contains text, and we are currently collecting an answer,
        # treat this as a continuation of the answer (e.g., an extra bullet point or line).
        if current_question and text:
            answer_lines.append(text)

# After loop, save the last Q&A pair if not already saved
if current_question is not None:
    full_answer = "\n".join(answer_lines).strip()
    qa_dict[current_question] = full_answer

# qa_dict now contains all questions as keys and their answers as values.
print(qa_dict)
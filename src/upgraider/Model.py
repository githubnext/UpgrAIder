# some code in this script is based off https://github.com/openai/openai-cookbook/blob/main/examples/Question_answering_using_embeddings.ipynb 

import numpy as np
import openai
import tiktoken
from os import environ as env
from dotenv import load_dotenv
from string import Template
import os
import re
from upgraider.Database import load_embeddings, get_embedded_doc_sections
from upgraider.Report import UpdateStatus, ModelResponse, DBSource
import logging as log
import requests
import json

load_dotenv(override=True)

EMBEDDING_MODEL = "text-embedding-ada-002"

#TODO: use token length
MAX_SECTION_LEN = 500
SEPARATOR = "\n* "

ENCODING = "cl100k_base"  # encoding for text-embedding-ada-002
 
encoding = tiktoken.get_encoding(ENCODING)
separator_len = len(encoding.encode(SEPARATOR))

COMPLETIONS_API_PARAMS = {
    "temperature": 0.0,
    "model": "code-cushman-001"
}

GPT_3_5_TURBO_API_PARAMS = {
    "temperature": 0.0,
    "max_tokens": 300,
    "model": "gpt-3.5-turbo"
}

def get_update_status(update_status: str) -> UpdateStatus:
    if update_status == "Update":
        return UpdateStatus.UPDATE
    elif update_status == "No update":
        return UpdateStatus.NO_UPDATE
    else:
        print(f"WARNING: unknown update status {update_status}")
        return UpdateStatus.UNKNOWN

def strip_python_keyword(code: str) -> str:
    """
    The model sometimes adds a python keyword to the beginning of the code snippet.
    This function removes that keyword.
    """
    if code.startswith("python"):
        return "\n".join(code.splitlines()[1:])
    else:
        return code

def find_reason_in_response(model_response: str) -> str:

    reason = None

    prefixes = ["Reason for update:"]
    # try first the case where the model respects the enumeration
    reason_matches = re.search(r"^2\.(.*)", model_response, re.MULTILINE) 
    reason = reason_matches.group(1).strip() if reason_matches else None

    if reason is not None:
        # check if reason starts with any of the prefixes and strip out the prefix
        for prefix in prefixes:
            if prefix in reason:
                reason = reason[len(prefix):].strip()
                break
    else:
        # did not have enumeration so let's try to search in the response
        for prefix in prefixes:
            reason_matches = re.search(r"^.*" + prefix + r"(.*)", model_response, re.MULTILINE)
            if reason_matches:
                matched_value = reason_matches.group(1).strip()
                # if the group is empty, then it just matched the prefix
                # then it still didn't capture the reasons (could be list)
                if matched_value != '':
                    reason = matched_value
                    break

            multi_reason_matches = re.search(r"^.*" + prefix + "\n*(?P<reasons>(-(.*)\n)+)", model_response, re.MULTILINE)
            if multi_reason_matches:
                reason = multi_reason_matches.group("reasons").strip()
                if len(reason.splitlines()) == 1 and reason.startswith("-"):
                    # if it's a single reason, remove the - since it's not
                    # really a list
                    reason = reason[1:].strip()
                break

    if reason == 'None':
        reason = None

    return reason

def find_references_in_response(model_response: str) -> str:
    references = None
    reference_keywords = ['Reference used:', 'Reference number:', 'References used:', 'Reference numbers used:', 'List of reference numbers used:']
    reference_matches = re.search(r"^3\.(.*)\n", model_response, re.MULTILINE)
    references = reference_matches.group(1).strip() if reference_matches else None

    # response did not follow enumerated format
    if references == None:
        for keyword in reference_keywords:
            if keyword in model_response:
                references = model_response.split(keyword)[1].strip()

                if references.strip('.') == 'No references used':
                    references = None
                
                break

    return references

    
def parse_model_response(model_response: str) -> ModelResponse:
    
    # match the updated code by looking for the fenced code block, even without the correct enumeration
    updated_code_response = re.search(r"\s*(```)\s*([\s\S]*?)(```|$)", model_response)
    updated_code = None
    if updated_code_response:
        updated_code = strip_python_keyword(updated_code_response.group(2).strip())
        if updated_code != "" and "No changes needed" not in updated_code:
            update_status = UpdateStatus.UPDATE
        else:
            update_status = UpdateStatus.NO_UPDATE
    else:
        if "No update" in model_response:
            update_status = UpdateStatus.NO_UPDATE
        else:
            update_status = UpdateStatus.NO_RESPONSE
    
    reason = find_reason_in_response(model_response)
    references = find_references_in_response(model_response) 

    response = ModelResponse(
        update_status = update_status,
        references = references,
        updated_code = updated_code,
        reason = reason
    )

    return response


def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    """
        Returns the embedding for the supplied text.
    """
    openai.api_key = env['OPENAI_API_KEY']

    try:
        result = openai.Embedding.create(model=model, input=text)
    except openai.error.InvalidRequestError as e:
        print(f"ERROR: {e}")
        return None
    
    return result["data"][0]["embedding"]


def vector_similarity(x: list[float], y: list[float]) -> float:
    """
    Returns the similarity between two vectors.

    Because OpenAI Embeddings are normalized to length 1, the cosine similarity is the same as the dot product.
    """
    if x is None or y is None:
        return 0.0
    return np.dot(np.array(x), np.array(y))

def get_reference_list(
    original_code: str,
    sections: list[DeprecationWarning],
    threshold: float = 0.0,
):
    chosen_sections = []
    chosen_sections_len = 0
    ref_count = 0

    context_embeddings = load_embeddings(sections)
        
    most_relevant_document_sections = order_document_sections_by_query_similarity(
        original_code, context_embeddings, threshold
    )

    for similarity, section_index in most_relevant_document_sections:

        if chosen_sections_len > MAX_SECTION_LEN:
            break

        # Add sections as context, until we run out of space.
        section_content = [
                section for section in sections if section.id == section_index][0].content

        section_tokens = section_content.split(" ")

        if len(section_tokens) < 3:
            continue # skip one or two word references

        len_if_added = chosen_sections_len + len(section_tokens) + separator_len

        # if current section will exceed max length, truncate it
        if len_if_added > MAX_SECTION_LEN:
            section_content = " ".join(
                section_tokens[: MAX_SECTION_LEN - chosen_sections_len]
            )

        chosen_sections_len = len_if_added
        ref_count += 1

        chosen_sections.append(
            "\n" + str(ref_count) + ". " + section_content.replace("\n", " ")
        )
    
    return chosen_sections

def get_readycontext_refs_list(
    ready_context: str  
):
    chosen_sections = []
    current_length = 0
    for context in ready_context:
        if current_length < MAX_SECTION_LEN:
            chosen_sections.append(
                "\n" + str(ref_count) + ". " + context.replace("\n", " ")
            )
            ref_count += 1
            current_length += len(context.split(" "))
    
    return ready_context

def order_document_sections_by_query_similarity(
    query: str, 
    contexts: dict[(int, int), np.array],
    threshold: float = None
) -> list[(float, (int, int))]:
    """
    Find the query embedding for the supplied query, and compare it against all of the pre-calculated document embeddings
    to find the most relevant sections.

    Return the list of document sections, sorted by relevance in descending order.
    """
    query_embedding = get_embedding(query)

    if query_embedding is None:
        return []

    document_similarities = sorted(
        [
            (vector_similarity(query_embedding, doc_embedding), doc_index)
            for doc_index, doc_embedding in contexts.items()
        ],
        reverse=True,
    )

    if threshold:
        document_similarities = [sim for sim in document_similarities if sim[0] > threshold]


    return document_similarities

def construct_fixing_prompt(
    original_code: str,
    sections: list[DeprecationWarning],
    ready_context: str = None,
    threshold: float = None,
):   
    # print("constructing prompt...")

    if not ready_context:
        references = get_reference_list(original_code=original_code, sections=sections, threshold=threshold)
    else:
       references = get_readycontext_refs_list(ready_context=ready_context)

    script_dir = os.path.dirname(__file__)
    with open(os.path.join(script_dir, "resources/chat_template.txt"), "r") as file:
        chat_template = Template(file.read())
        prompt_text = chat_template.substitute(original_code=original_code, references="".join(references))

    return prompt_text, len(references)

def display_conversation(messages: list[dict[str, str]]):
    for message in messages:
        print(message["role"] + ": " + message["content"] + '\n')

def fix_suggested_code(
    query: str,
    show_prompt: bool = False,
    db_source: str = DBSource.documentation,
    model: str = "gpt-3.5",
    threshold: float = None,
    ready_context: str = None,
) :
    
    sections = None
    if not ready_context:
        if db_source == DBSource.documentation:
            sections = get_embedded_doc_sections()
        elif db_source == DBSource.modelonly:
            sections = []
        else:
            raise ValueError(f"Invalid db_source {db_source}")
    
    prompt_text, ref_count = construct_fixing_prompt(original_code=query, sections=sections, ready_context=ready_context, threshold=threshold)
        
    if model == "gpt-3.5": 
        prompt = [
            {"role": "system", "content":"You are a smart code reviewer who can spot code that uses a non-existent or deprecated API."},
            {"role": "user", "content": prompt_text}
        ]
        model_response, parsed_response = fix_suggested_code_chat(prompt)    
    elif model == "gpt-4":
        model_response, parsed_response = fix_suggested_code_completion(prompt_text)
    
    return prompt_text, model_response, parsed_response, ref_count


    
def fix_suggested_code_chat(
    prompt: list[str]
) :
    # print("Fixing code with chat API....")

    openai.api_key = env['OPENAI_API_KEY']
   
    response = openai.ChatCompletion.create(messages=prompt, **GPT_3_5_TURBO_API_PARAMS)
    response_text = response['choices'][0]['message']['content']
    
    return response_text, parse_model_response(response_text)

def fix_suggested_code_completion(
    prompt: str
) -> str:
    gpt4_endpoint = env['GPT4_ENDPOINT']
    auth_headers = env['GPT4_AUTH_HEADERS']
    headers = {
      "Content-Type": "application/json",
       **json.loads(auth_headers),
    }
    json_data = {
        'prompt': prompt,
        'temperature': 0,
        'best_of': 1,
        'max_tokens': 300
    }

    response = requests.post(gpt4_endpoint, headers=headers, data=json.dumps(json_data)).json()
    response_text = response['choices'][0]['text'].strip(" \n")
    return response_text, parse_model_response(response_text)

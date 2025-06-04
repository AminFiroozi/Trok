import json
import os
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import chromadb
from sentence_transformers import SentenceTransformer

from autogen import ConversableAgent, LLMConfig
from autogen.agentchat.contrib.retrieve_assistant_agent import AssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen import GroupChat, GroupChatManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_messages_from_json(json_path: str) -> List[str]:
    """
    Load messages from a JSON file and format them for the retriever.
    
    Args:
        json_path (str): Path to the JSON file containing messages
        
    Returns:
        List[str]: List of formatted message strings
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        formatted_messages = []
        
        # Process messages from the JSON structure
        for conversation in data.get('messages', {}).get('most_recent', {}).values():
            for message in conversation:
                if 'text' in message and message['text'].strip():
                    formatted_message = (
                        f"Sender: {message.get('name', 'Unknown')}\n"
                        f"Content: {message['text']}\n"
                        f"Timestamp: {message.get('date', 'Unknown')}\n"
                    )
                    formatted_messages.append(formatted_message)
        # print(formatted_messages)
        return formatted_messages
    except Exception as e:
        logger.error(f"Error loading messages from JSON: {str(e)}")
        raise


def setup_rag_system(config_path: str, messages: List[str]) -> Tuple[RetrieveUserProxyAgent, RetrieveUserProxyAgent, GroupChatManager]:
    try:
        with open(config_path) as f:
            config = json.load(f)

        OPENAI_API_KEY = config["api_key"]
        BASE_URL = config["base_url"]
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        os.environ["OPENAI_BASE_URL"] = BASE_URL

        llm_config = LLMConfig(api_type="openai", model="gpt-4")

        # Configure ChromaDB client with proper settings
        chroma_settings = Settings(
            persist_directory="/tmp/chromadb",
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True
        )
        
        client = chromadb.PersistentClient(path="/tmp/chromadb", settings=chroma_settings)

        # Initialize SentenceTransformer model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create custom embedding function using SentenceTransformer
        class SentenceTransformerEmbeddingFunction(embedding_functions.EmbeddingFunction):
            def __init__(self, model):
                self.model = model
                
            def __call__(self, texts):
                embeddings = self.model.encode(texts)
                return embeddings.tolist()

        # Configure embedding function
        sentence_transformer_ef = SentenceTransformerEmbeddingFunction(model)

        assistant = AssistantAgent(
            name="assistant",
            system_message="assistant. You are a helpful assistant. You retrieve knowledge from a text. You should pay attention to all the details.",
            llm_config=llm_config,
        )

        reviewer = AssistantAgent(
            name="reviewer",
            system_message="reviewer. double-check the response from the assistant for correctness.\nReturn 'TERMINATE' in the end when the task is over.",
            llm_config=llm_config,
        )

        # Create a single RAG proxy agent for all messages
        ragproxyagent = RetrieveUserProxyAgent(
            human_input_mode="NEVER",
            name="ragproxyagent",
            retrieve_config={
                "task": "qa",
                "docs_path": './all_messages.json',  # Pass the formatted messages directly
                "embedding_function": sentence_transformer_ef,
                "client": client,
                "model": "gpt-4",
                "overwrite": True,
                "get_or_create": True,
                "collection_settings": {
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 100,
                    "hnsw:search_ef": 50
                }
            },
            code_execution_config=False,
        )

        groupchat_rag = GroupChat(
            agents=[ragproxyagent, assistant, reviewer],
            messages=[],
            max_round=20,
            speaker_selection_method='auto'
        )

        manager_rag = GroupChatManager(
            groupchat=groupchat_rag,
            llm_config=llm_config,
            system_message='You dynamically select a speaker based on the context.'
        )
        
        return ragproxyagent, manager_rag

    except Exception as e:
        logger.error(f"Error setting up RAG system: {str(e)}")
        raise


def query_chat_messages(question: str, messages) -> str:
    try:
        ragproxyagent, manager_rag = setup_rag_system("./config.json", messages)
        res = ragproxyagent.initiate_chat(
            manager_rag,
            message=ragproxyagent.message_generator,
            problem=question,
            clear_history=True,
            silent=False,
            summary_method="reflection_with_llm",
            summary_args={"summary_prompt": "Fully return the retrieved knowledge"}
        )
        return res.summary
    except Exception as e:
        logger.error(f"Error querying chat messages: {str(e)}")
        raise

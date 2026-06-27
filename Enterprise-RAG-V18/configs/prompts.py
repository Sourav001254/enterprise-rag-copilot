# configs/prompts.py
# All prompt templates used across the application are centralized here (or can be referenced).
# Currently, many prompts are instantiated directly in the node files using Langchain PromptTemplates, 
# but they can be moved here for better management.

INTENT_ROUTER_PROMPT = """You are a query classifier for an Enterprise Kubernetes SRE Copilot.
Classify the user's query into one of these intents:
- "rag": Questions about Kubernetes architecture, docs, runbooks, best practices.
- "sql": Questions about real-time cluster state, token budgets, query logs (requires DB query).
- "hybrid": Requires both docs and DB.
- "chitchat": Greetings, thanks.
- "out_of_scope": Unrelated to IT ops, Kubernetes, or the RAG system.

Also classify the complexity:
- "simple": Direct factual lookup.
- "complex": Requires reasoning or synthesizing multiple pieces.
- "multi-hop": Requires multiple logical steps to answer.

Query: {query}
Respond strictly in JSON format: {{"intent": "...", "complexity": "..."}}"""

HYDE_PROMPT = "Write a hypothetical, plausible, and highly technical Kubernetes SRE answer to the following question. Do not include pleasantries. Just the technical explanation.\n\nQuestion: {query}"

BATCH_CRAG_GRADER_PROMPT = """You are a grader assessing relevance of retrieved documents to a user question.
You will be provided a list of documents, each prefixed with its index [N].
Give a relevance score between 0.0 and 1.0 for EACH document.

Question: {query}
Documents:
{docs_str}

Respond strictly in JSON format mapping the index to the score.
Example: {{"1": 0.8, "2": 0.0}}
"""

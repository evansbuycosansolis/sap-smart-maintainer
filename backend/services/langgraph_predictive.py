
from services.vectorstore_manager import get_faiss_index
from langgraph.graph import StateGraph
from typing import TypedDict, List, Optional

class PredictiveState(TypedDict, total=False):
    input: dict
    context_docs: Optional[List]
    context_warning: Optional[str]
    ml_result: Optional[dict]
    action: Optional[str]

graph = StateGraph(PredictiveState)



# ---- 1. Node: Context Retrieval (FAISS) ----
def retrieve_context(state):
    question = state['input'].get('analysis_question', 'Give me relevant maintenance data')
    vectorstore = get_faiss_index()
    if not vectorstore:
        state['context_docs'] = []
        state['context_warning'] = "No FAISS index loaded"
        return state
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    docs = retriever.get_relevant_documents(question)
    state['context_docs'] = docs
    return state

# ---- 2. Node: Predictive ML/Stats Model ----
def run_predictive_model(state):
    # This is a stub – replace with your own ML/stat analysis
    logs = state['input'].get('sensor_log_text', '')
    history = state.get('context_docs', [])
    # Example: dummy ML logic
    risk_score = 0.85 if "fault" in logs.lower() else 0.23
    predicted_failure = "Bearing Wear" if risk_score > 0.7 else "None"
    recommendation = "Create SAP Work Order" if risk_score > 0.7 else "Continue monitoring"
    state['ml_result'] = {
        "risk_score": risk_score,
        "predicted_failure": predicted_failure,
        "recommendation": recommendation
    }
    return state

# ---- 3. Node: LLM (optional rule/LLM judgment) ----
def llm_judgement(state):
    ml = state['ml_result']
    if ml['risk_score'] > 0.75:
        action = "Escalate: Create urgent SAP work order."
    else:
        action = "No urgent action. Log and monitor."
    state['action'] = action
    return state

# ---- 4. Node: Output Aggregator ----
def output_node(state):
    return {
        "analysis": state.get('ml_result'),
        "action": state.get('action'),
        "context_snippet": [
            doc.page_content[:250] for doc in state.get('context_docs', [])
        ],
        "context_warning": state.get('context_warning')
    }

# ---- Build the workflow graph ----
graph = StateGraph(PredictiveState)
graph.add_node("context_retrieval", retrieve_context)
graph.add_node("predictive_model", run_predictive_model)
graph.add_node("llm_judgement", llm_judgement)
graph.add_node("output", output_node)
graph.add_edge("context_retrieval", "predictive_model")
graph.add_edge("predictive_model", "llm_judgement")
graph.add_edge("llm_judgement", "output")
graph.add_edge("__start__", "context_retrieval")

# ---- Entrypoint for your backend ----
def run_predictive_workflow(sensor_log_text, question=None):
    """
    sensor_log_text: str – parsed PDF sensor log as plain text
    question: str – what analysis to retrieve (optional)
    Returns: dict – workflow output
    """
    input_dict = {
        "analysis_question": question or "Analyze last 24 hours of equipment logs for anomalies.",
        "sensor_log_text": sensor_log_text
    }
    state = {"input": input_dict}
    compiled_graph = graph.compile()
    result = compiled_graph.invoke(state)
    return result

# ---- (Optional) Test ----
if __name__ == "__main__":
    # Simulate a PDF log text (replace with your PDF extraction logic)
    fake_log = "2024-06-12 14:30, sensor_1: 1.22g, sensor_2: 45C, fault detected: Vibration Spike"
    workflow_output = run_predictive_workflow(fake_log, "Show risk and action for last 24h.")
    import pprint; pprint.pprint(workflow_output)

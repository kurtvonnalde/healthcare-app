Azure OpenAI resource
2 deployments 
	• Embedding model → for AI Search indexing & retrieval
	• Chat model (GPT‑4 / GPT‑4o) → for answering questions
 API keys + endpoint ready for use in: 
	• Azure AI Search
	• Local Python (FastAPI)
	• Azure App Service
STEPS
Create Azure OpenAI Resource
	• Azure Portal → Create a resource
	• Search: Azure OpenAI
	• Click Create
Create Embedding Model Deployment
This deployment will be used by Azure AI Search to generate vectors.
	1. Open Azure OpenAI Studio 
		○ From the resource → Go to Azure OpenAI Studio
	2. Go to Deployments
	3. Click Create new deployment
Embedding deployment settings
	• Model: text-embedding-3-large
	• Deployment name:  embed-health-rag
	• Version: default
	• Tokens per minute (TPM): default is fine
Click Create

Create Chat Model Deployment
This is what your app will call to generate healthcare answers.
	1. Still in Deployments
	2. Click Create new deployment
Chat deployment settings
Choose one of these:
✅ Recommended (balanced)
	• Model: gpt-4o
	• Deployment name: chat-health-rag
OR
Leave defaults → Create

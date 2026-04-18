# Future Roadmap

Development priorities revolve around expanding the vector classification mechanics into structured retrieval capabilities and improving metadata persistence.

## Knowledge Retrieval
*Objective: Utilize the existing FAISS index to support query-based file retrieval.*
- **Contextual Search**: Rather than solely computing embeddings to route files, the system will support localized querying of the FAISS index against constrained language models. This integration will extract and retrieve specific file strings or summaries relevant to user search queries.

## Contextual Association Among Files
*Objective: To understand the relationships between distinct files to achieve a broader context and aid in agentic automations.*
- **Graph-Based Linking**: Establish relational links between files that share semantic clusters or sequential metadata. This shifts the paradigm from isolated document sorting to interconnected knowledge graphing.
- **Agentic Workflows**: By mapping file associations, the system will serve as a foundational data layer for autonomous agents. This allows localized language models to synthesize project-wide summaries, infer cross-document dependencies, and execute multi-file processing pipelines automatically.

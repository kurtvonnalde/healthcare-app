Azure Storage Account
Set up Storage in a clean way, with both structured + unstructured.
Steps
    Create Storage Account
        • Azure Portal → Storage accounts → Create
        • Resource group: rg-health-rag-demo
        • Name: sthealthrag<unique>
        • Region: same as above
        • Performance: Standard
        • Redundancy: LRS
    Create Blob Containers (organized by data type)
        Go to Storage Account → Data storage → Containers → + Container:
        Create these:
            • unstructured-docs
            • structured-data
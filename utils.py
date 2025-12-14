def preprocess_documents(documents):
    processed = []
    for doc in documents:
        # Combine title, headings, and text
        content_parts = [doc.get('title', '')] + doc.get('headings', []) + [doc.get('text', '')]
        content = ' '.join(part for part in content_parts if part)
        # Clean: remove extra whitespace
        content = ' '.join(content.split())
        processed.append({
            'url': doc['url'],
            'content': content
        })
    return processed
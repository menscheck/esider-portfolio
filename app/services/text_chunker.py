class TextChunker:

    def chunk(self, text, chunk_size=300):
        chunks = []

        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i+chunk_size])

        return chunks

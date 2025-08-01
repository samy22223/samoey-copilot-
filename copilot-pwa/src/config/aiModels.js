export const LLM_OPTIONS = {
  // GPT Family
  'GPT-2': { id: 'gpt2', source: 'OpenAI', params: '124M-1.5B', free: true },
  'GPT-J': { id: 'gpt-j-6b', source: 'EleutherAI', params: '6B', free: true },
  'GPT-Neo': { id: 'gpt-neo', source: 'EleutherAI', params: '1.3B/2.7B', free: true },
  'GPT-NeoX': { id: 'gpt-neox-20b', source: 'EleutherAI', params: '20B', free: true },

  // Meta & Misc
  'LLaMA 3': { id: 'meta-llama-3', source: 'Meta', params: '7B-70B', free: true },
  'Bloom': { id: 'bloom', source: 'BigScience', params: '560M-176B', free: true },
  'Falcon': { id: 'falcon', source: 'TII', params: '7B-40B', free: true },
  'MPT': { id: 'mpt', source: 'MosaicML', params: '7B-30B', free: true },

  // Encoder-Decoder
  'T5': { id: 't5', source: 'Google', params: 'Small-3B', free: true },
  'Flan-T5': { id: 'flan-t5', source: 'Google', params: 'Small-XXL', free: true },
  'BART': { id: 'bart', source: 'Facebook', params: 'Base-Large', free: true },

  // Encoder-Only
  'BERT': { id: 'bert', source: 'Google', params: 'Base-Large', free: true },
  'RoBERTa': { id: 'roberta', source: 'Facebook', params: 'Base-Large', free: true },
  'XLNet': { id: 'xlnet', source: 'Google', params: 'Base-Large', free: true },

  // Fine-tuned
  'Alpaca': { id: 'alpaca', source: 'Stanford', params: '7B', free: true },
  'Vicuna': { id: 'vicuna', source: 'Community', params: '13B', free: true }
}

export const EMBEDDING_MODELS = {
  'Instructor XL': { id: 'instructor-xl', dims: 768, library: 'sentence-transformers' },
  'All-MiniLM': { id: 'all-minilm', dims: 384, library: 'sentence-transformers' },
  'BGE Small': { id: 'bge-small', dims: 384, library: 'fastembed' },
  'E5': { id: 'e5', dims: 768, library: 'sentence-transformers' }
}

export const VISION_MODELS = {
  'CLIP': { id: 'openai/clip', tasks: ['image-text'] },
  'BLIP': { id: 'blip', tasks: ['captioning', 'vqa'] }
}

export const AUDIO_MODELS = {
  'Whisper': { id: 'openai/whisper', tasks: ['asr'] },
  'Wav2Vec': { id: 'facebook/wav2vec', tasks: ['asr'] }
}

export const TOOL_MODELS = {
  'ChromaDB': { id: 'chromadb', type: 'vector-store' },
  'FAISS': { id: 'faiss', type: 'vector-store' },
  'LlamaIndex': { id: 'llamaindex', type: 'knowledge-base' }
}

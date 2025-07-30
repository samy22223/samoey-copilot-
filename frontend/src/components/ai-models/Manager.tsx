import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ModelInfo {
  name: string;
  type: string;
  provider: string;
  model_size: string;
  languages: string[];
  is_local: boolean;
}

interface ModelsByType {
  [key: string]: ModelInfo[];
}

export default function AIModelsManager() {
  const [models, setModels] = useState<ModelsByType>({});
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await axios.get('/api/models');
      setModels(response.data);
    } catch (error) {
      console.error('Error fetching models:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateOutput = async (type: string) => {
    if (!selectedModel || !input) return;

    try {
      const response = await axios.post(`/api/generate/${type}`, {
        model_name: selectedModel,
        input_data: input,
      });
      setResult(response.data);
    } catch (error) {
      console.error(`Error generating ${type}:`, error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">AI Models Manager</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Model Selection */}
        <div className="space-y-4">
          {Object.entries(models).map(([type, modelList]) => (
            <div key={type} className="border rounded-lg p-4">
              <h2 className="text-xl font-semibold mb-4 capitalize">{type} Models</h2>
              <div className="space-y-2">
                {modelList.map((model) => (
                  <div
                    key={model.name}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedModel === model.name
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                    onClick={() => setSelectedModel(model.name)}
                  >
                    <div className="font-medium">{model.name}</div>
                    <div className="text-sm">
                      Size: {model.model_size} | Provider: {model.provider}
                    </div>
                    {model.languages.length > 0 && (
                      <div className="text-sm">
                        Languages: {model.languages.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Input and Generation */}
        <div className="space-y-4">
          <div className="border rounded-lg p-4">
            <h2 className="text-xl font-semibold mb-4">Generate Output</h2>
            <textarea
              className="w-full h-32 p-2 border rounded-lg mb-4"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter your prompt..."
            />
            <div className="space-x-2">
              <button
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
                onClick={() => generateOutput('text')}
              >
                Generate Text
              </button>
              <button
                className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600"
                onClick={() => generateOutput('code')}
              >
                Generate Code
              </button>
              <button
                className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600"
                onClick={() => generateOutput('image')}
              >
                Generate Image
              </button>
            </div>
          </div>

          {/* Results */}
          {result && (
            <div className="border rounded-lg p-4">
              <h2 className="text-xl font-semibold mb-4">Result</h2>
              <pre className="bg-gray-100 p-4 rounded-lg overflow-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

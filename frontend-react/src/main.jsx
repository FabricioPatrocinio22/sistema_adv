import React from 'react'
import ReactDOM from 'react-dom/client'
import { ChakraProvider } from '@chakra-ui/react' // <--- IMPORTANTE
import App from './App.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ChakraProvider> {/* <--- IMPORTANTE: Envelopando o App */}
      <App />
    </ChakraProvider>
  </React.StrictMode>,
)
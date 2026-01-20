// src/App.jsx
import { useState } from 'react'
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom'
import { 
  Box, Button, Input, Heading, VStack, Text, useToast, Container, Link, HStack, Divider 
} from '@chakra-ui/react'
import axios from 'axios'
import Dashboard from './Dashboard'
import Processos from './Processos'
import Clientes from './Clientes'
import Financeiro from './Financeiro' // <--- 1. Importa

function Login() {
  // Estados dos campos
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [confirmarSenha, setConfirmarSenha] = useState('') // Novo campo
  
  // Estados de controle visual
  const [loading, setLoading] = useState(false)
  const [isLogin, setIsLogin] = useState(true) // true = Login, false = Cadastro

  const toast = useToast()
  const navigate = useNavigate()

  // 1. Lógica de LOGIN (Já existia)
  const handleLogin = async () => {
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', senha)

      // Ajuste a porta se necessário
      const response = await axios.post('http://127.0.0.1:8000/token', formData)
      
      localStorage.setItem('token', response.data.access_token)
      toast({ title: 'Bem-vindo(a)!', status: 'success', duration: 2000 })
      navigate('/dashboard')

    } catch (error) {
      toast({ title: 'Erro ao entrar', description: "Verifique seus dados.", status: 'error' })
    }
    setLoading(false)
  }

  // 2. Lógica de CADASTRO (Nova) 🆕
  const handleCadastro = async () => {
    // Validação básica no Frontend
    if (senha !== confirmarSenha) {
      toast({ title: 'Senhas não conferem', status: 'warning' })
      return
    }
    if (senha.length < 4) {
      toast({ title: 'Senha muito curta', status: 'warning' })
      return
    }

    setLoading(true)
    try {
      // O payload deve bater com o "UsuarioCreate" do seu backend Python
      const payload = {
        email: email,
        senha: senha
      }

      await axios.post('http://127.0.0.1:8000/usuarios', payload)
      
      toast({ 
        title: 'Conta criada!', 
        description: "Agora faça login para entrar.", 
        status: 'success',
        duration: 4000,
        isClosable: true
      })
      
      // Volta para a tela de login automaticamente para a pessoa entrar
      setIsLogin(true)
      setSenha('')
      setConfirmarSenha('')

    } catch (error) {
      // Tenta pegar a mensagem de erro específica do Python (ex: "Email já existe")
      const msgErro = error.response?.data?.detail || "Erro ao criar conta."
      toast({ title: 'Erro', description: msgErro, status: 'error' })
    }
    setLoading(false)
  }

  return (
    <Box w="100vw" h="100vh" bg="gray.50" display="flex" alignItems="center" justifyContent="center">
      <Container maxW="md" bg="white" p={8} borderRadius="lg" shadow="lg">
        <VStack spacing={5}>
          
          {/* Título Dinâmico */}
          <Heading color="blue.600" size="lg">
            {isLogin ? "⚖️ Acesso Jurídico" : "📝 Criar Nova Conta"}
          </Heading>
          
          <Text color="gray.500" fontSize="sm">
            {isLogin ? "Gerencie seus processos com IA" : "Junte-se ao futuro da advocacia"}
          </Text>

          {/* Campos */}
          <Input 
            placeholder="E-mail" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            size="lg" 
          />
          
          <Input 
            placeholder="Senha" 
            type="password" 
            value={senha} 
            onChange={(e) => setSenha(e.target.value)} 
            size="lg" 
          />

          {/* Campo Extra só aparece no modo Cadastro */}
          {!isLogin && (
            <Input 
              placeholder="Confirme a Senha" 
              type="password" 
              value={confirmarSenha} 
              onChange={(e) => setConfirmarSenha(e.target.value)} 
              size="lg" 
            />
          )}

          {/* Botão de Ação Dinâmico */}
          <Button 
            colorScheme="blue" 
            size="lg" 
            w="full" 
            onClick={isLogin ? handleLogin : handleCadastro} 
            isLoading={loading}
          >
            {isLogin ? "Entrar no Sistema" : "Cadastrar-se"}
          </Button>

          <Divider />

          {/* Link para Trocar de Modo */}
          <HStack fontSize="sm">
            <Text>
              {isLogin ? "Ainda não tem conta?" : "Já possui cadastro?"}
            </Text>
            <Link 
              color="blue.500" 
              fontWeight="bold" 
              onClick={() => setIsLogin(!isLogin)} // <--- Aqui acontece a mágica da troca
            >
              {isLogin ? "Criar conta grátis" : "Fazer Login"}
            </Link>
          </HStack>

        </VStack>
      </Container>
    </Box>
  )
}

// --- O CONTROLADOR DE ROTAS ---
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/processos" element={<Processos />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/financeiro" element={<Financeiro />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
import { useEffect, useState } from 'react'
import { 
  Box, Flex, Heading, Text, SimpleGrid, Stat, StatLabel, StatNumber, StatHelpText, 
  Icon, VStack, HStack, Button, Avatar, Divider, Skeleton, useToast 
} from '@chakra-ui/react'
import { FiHome, FiFileText, FiUsers, FiDollarSign, FiLogOut } from 'react-icons/fi' // Ícones bonitos
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'

// --- COMPONENTE CARD DE KPI (OS QUADRADINHOS) ---
const KPICard = ({ label, value, help, isLoading }) => (
  <Box bg="white" p={5} shadow="sm" borderRadius="lg" border="1px" borderColor="gray.100">
    <Skeleton isLoaded={!isLoading}>
      <Stat>
        <StatLabel color="gray.500">{label}</StatLabel>
        <StatNumber fontSize="2xl" color="blue.700">{value}</StatNumber>
        {help && <StatHelpText>{help}</StatHelpText>}
      </Stat>
    </Skeleton>
  </Box>
)

// --- TELA PRINCIPAL ---
function Dashboard() {
  const navigate = useNavigate()
  const toast = useToast()
  
  // ESTADOS (A Memória)
  const [dados, setDados] = useState(null) // Começa vazio
  const [loading, setLoading] = useState(true)

  // O GARÇOM (Busca os dados assim que abre)
  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        navigate('/') // Se não tem crachá, tchau
        return
      }

      // Chama o Backend Python
      const response = await axios.get('http://127.0.0.1:8000/dashboard/geral', {
        headers: { Authorization: `Bearer ${token}` } // Mostra o crachá
      })

      setDados(response.data) // Guarda o menu na memória
      
    } catch (error) {
      toast({ title: 'Erro ao carregar', status: 'error' })
      if (error.response?.status === 401) {
        navigate('/') // Token venceu
      }
    } finally {
      setLoading(false) // Garçom voltou, pode parar de rodar a ampulheta
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/')
  }

  return (
    <Box bg="gray.50" minH="100vh">
      {/* 1. Menu Lateral */}
      <Sidebar/>

      {/* 2. Conteúdo Principal (Empurrado 250px para a direita) */}
      <Box ml="250px" p={8}>
        
        {/* Cabeçalho */}
        <Flex justify="space-between" align="center" mb={8}>
          <Box>
            <Heading size="lg" color="gray.700">Visão Geral</Heading>
            <Text color="gray.500">Bem-vindo de volta, Doutor(a).</Text>
          </Box>
          <Avatar name="Advogado" bg="blue.500" color="white" />
        </Flex>

        {/* Grid de Cards (KPIs) */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={5} mb={8}>
          <KPICard 
            label="Total de Processos" 
            value={dados?.total || 0} 
            help={`${dados?.ativos || 0} Ativos`} 
            isLoading={loading} 
          />
          <KPICard 
            label="Prazos Vencidos" 
            value={dados?.vencidos || 0} 
            help="Atenção Imediata" 
            isLoading={loading} 
          />
          <KPICard 
            label="Honorários Pendentes" 
            value={`R$ ${dados?.total_honorarios || 0}`} 
            help="A receber" 
            isLoading={loading} 
          />
          <KPICard 
            label="Recebido (Caixa)" 
            value={`R$ ${dados?.total_recebido || 0}`} 
            help="Confirmado" 
            isLoading={loading} 
          />
        </SimpleGrid>

        {/* Área de Gráficos e Listas (Placeholder por enquanto) */}
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={5}>
          <Box bg="white" p={6} borderRadius="lg" shadow="sm" h="300px">
            <Heading size="md" mb={4}>📅 Próximos Prazos</Heading>
            {loading ? <Skeleton height="20px" count={3} /> : (
              <VStack align="start">
                {dados?.proximos_prazos?.length > 0 ? (
                    dados.proximos_prazos.map((prazo, i) => (
                        <Text key={i}>🔴 {prazo.numero} - {prazo.cliente}</Text>
                    ))
                ) : (
                    <Text color="gray.500">Nenhum prazo urgente.</Text>
                )}
              </VStack>
            )}
          </Box>

          <Box bg="white" p={6} borderRadius="lg" shadow="sm" h="300px">
            <Heading size="md" mb={4}>📊 Status dos Processos</Heading>
            <Text color="gray.400">Gráfico será implementado em breve.</Text>
          </Box>
        </SimpleGrid>

      </Box>
    </Box>
  )
}

export default Dashboard
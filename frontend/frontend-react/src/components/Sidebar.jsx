// src/components/Sidebar.jsx
import { Box, Heading, Text, Icon, VStack, HStack, Button, Divider } from '@chakra-ui/react'
import { FiHome, FiFileText, FiUsers, FiDollarSign, FiLogOut } from 'react-icons/fi'
import { useNavigate, useLocation } from 'react-router-dom'

const Sidebar = () => {
  const navigate = useNavigate()
  const location = useLocation() // Descobre em qual página estamos

  const menuItems = [
    { name: 'Visão Geral', icon: FiHome, path: '/dashboard' },
    { name: 'Meus Processos', icon: FiFileText, path: '/processos' }, // Rota nova
    { name: 'Clientes', icon: FiUsers, path: '/clientes' },
    { name: 'Financeiro', icon: FiDollarSign, path: '/financeiro' },
  ]

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/')
  }

  return (
    <Box w="250px" bg="white" h="100vh" borderRight="1px" borderColor="gray.200" pos="fixed" left={0} top={0} zIndex={1000}>
      <VStack spacing={8} align="stretch" p={6}>
        <Heading size="md" color="blue.600">⚖️ Advogado SaaS</Heading>
        
        <VStack spacing={2} align="stretch">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <HStack 
                key={item.path} 
                p={3} 
                borderRadius="md" 
                bg={isActive ? "blue.50" : "transparent"} 
                color={isActive ? "blue.600" : "gray.600"}
                cursor="pointer"
                _hover={{ bg: "gray.50" }}
                onClick={() => navigate(item.path)} // Navega de verdade agora
              >
                <Icon as={item.icon} />
                <Text fontWeight={isActive ? "bold" : "normal"}>{item.name}</Text>
              </HStack>
            )
          })}
        </VStack>

        <Divider />
        
        <Button leftIcon={<FiLogOut />} variant="ghost" colorScheme="red" onClick={handleLogout}>
          Sair
        </Button>
      </VStack>
    </Box>
  )
}

export default Sidebar
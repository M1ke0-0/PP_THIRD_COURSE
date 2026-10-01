import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded'
import CodeRoundedIcon from '@mui/icons-material/CodeRounded'
import {
  AppBar,
  Box,
  Chip,
  Container,
  Paper,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'

const technologies = ['React', 'Vite', 'Material UI', 'React Router', 'Axios']

export function HomePage() {
  return (
    <Box minHeight="100vh">
      <AppBar color="transparent" elevation={0} position="static">
        <Toolbar sx={{ maxWidth: 1200, width: '100%', mx: 'auto' }}>
          <CodeRoundedIcon color="primary" sx={{ mr: 1.5 }} />
          <Typography color="text.primary" fontWeight={750} variant="h6">
            Онлайн-тестирование
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ py: { xs: 7, md: 12 } }}>
        <Paper
          elevation={0}
          sx={{
            border: '1px solid',
            borderColor: 'divider',
            overflow: 'hidden',
            p: { xs: 3, sm: 6 },
            position: 'relative',
          }}
        >
          <Box
            sx={{
              bgcolor: 'primary.main',
              borderRadius: '50%',
              filter: 'blur(60px)',
              height: 220,
              opacity: 0.12,
              position: 'absolute',
              right: -80,
              top: -120,
              width: 220,
            }}
          />

          <Stack spacing={3} position="relative">
            <Chip
              color="success"
              icon={<CheckCircleRoundedIcon />}
              label="Каркас frontend готов"
              sx={{ alignSelf: 'flex-start' }}
            />
            <Typography component="h1" variant="h1" sx={{ fontSize: { xs: 38, sm: 56 } }}>
              Система для проведения онлайн-тестирования
            </Typography>
            <Typography color="text.secondary" fontSize={19} maxWidth={680}>
              Основа клиентского приложения настроена. Следующий этап — авторизация и
              маршрутизация интерфейса по ролям преподавателя и студента.
            </Typography>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              {technologies.map((technology) => (
                <Chip key={technology} label={technology} variant="outlined" />
              ))}
            </Stack>
          </Stack>
        </Paper>
      </Container>
    </Box>
  )
}


import { Button, Container, Stack, Typography } from '@mui/material'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <Container maxWidth="sm" sx={{ py: 12 }}>
      <Stack alignItems="flex-start" spacing={2}>
        <Typography color="primary" fontWeight={700}>
          Ошибка 404
        </Typography>
        <Typography component="h1" variant="h3">
          Страница не найдена
        </Typography>
        <Typography color="text.secondary">
          Проверьте адрес или вернитесь на стартовую страницу.
        </Typography>
        <Button component={Link} to="/" variant="contained">
          На главную
        </Button>
      </Stack>
    </Container>
  )
}


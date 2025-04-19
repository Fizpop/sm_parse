import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  Link,
  Box,
} from '@mui/material';
import NewReleasesIcon from '@mui/icons-material/NewReleases';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

interface MediaResult {
  title: string;
  link: string;
  domain: string;
  description: string;
  is_new: boolean;
}

interface SearchResultsProps {
  results: MediaResult[];
}

const SearchResults: React.FC<SearchResultsProps> = ({ results }) => {
  if (!results.length) {
    return null;
  }

  return (
    <Paper elevation={3} sx={{ mt: 3, p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Результати пошуку
      </Typography>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Назва</TableCell>
              <TableCell>Домен</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Опис</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.map((result, index) => (
              <TableRow key={index} hover>
                <TableCell>
                  <Link
                    href={result.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    color="primary"
                    underline="hover"
                  >
                    {result.title}
                  </Link>
                </TableCell>
                <TableCell>{result.domain}</TableCell>
                <TableCell>
                  <Chip
                    icon={result.is_new ? <NewReleasesIcon /> : <CheckCircleIcon />}
                    label={result.is_new ? 'Нове джерело' : 'Відоме джерело'}
                    color={result.is_new ? 'primary' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box
                    sx={{
                      maxWidth: '400px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {result.description}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        Знайдено результатів: {results.length}
      </Typography>
    </Paper>
  );
};

export default SearchResults; 
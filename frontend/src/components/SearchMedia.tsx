import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  CircularProgress,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

interface SearchMediaProps {
  onSearch: (query: string) => Promise<void>;
  isLoading: boolean;
}

const SearchMedia: React.FC<SearchMediaProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, my: 2 }}>
      <Typography variant="h6" gutterBottom>
        Пошук нових медіа
      </Typography>
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          display: 'flex',
          gap: 2,
          alignItems: 'flex-start',
        }}
      >
        <TextField
          fullWidth
          label="Пошуковий запит"
          variant="outlined"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Наприклад: українські новинні сайти 2024"
          disabled={isLoading}
        />
        <Button
          type="submit"
          variant="contained"
          startIcon={isLoading ? <CircularProgress size={20} /> : <SearchIcon />}
          disabled={!query.trim() || isLoading}
          sx={{ height: 56 }}
        >
          {isLoading ? 'Пошук...' : 'Шукати'}
        </Button>
      </Box>
    </Paper>
  );
};

export default SearchMedia; 
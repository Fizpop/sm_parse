import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  AppBar,
  Toolbar,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Alert,
  Snackbar,
  Tabs,
  Tab,
} from '@mui/material';
import FileUpload from './components/FileUpload';
import SearchMedia from './components/SearchMedia';
import SearchResults from './components/SearchResults';
import SourcesList from './components/SourcesList';
import NewspaperIcon from '@mui/icons-material/Newspaper';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface MediaResult {
  title: string;
  link: string;
  domain: string;
  description: string;
  is_new: boolean;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

function App() {
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<MediaResult[]>([]);
  const [notification, setNotification] = useState<{
    message: string;
    type: 'success' | 'error';
    open: boolean;
  }>({
    message: '',
    type: 'success',
    open: false,
  });
  const [tabValue, setTabValue] = useState(0);

  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({
      message,
      type,
      open: true,
    });
  };

  const handleCloseNotification = () => {
    setNotification((prev) => ({ ...prev, open: false }));
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload-csv`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      
      if (response.ok) {
        showNotification('Файл успішно завантажено', 'success');
      } else {
        throw new Error(data.detail || 'Помилка завантаження файлу');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      showNotification(
        error instanceof Error ? error.message : 'Помилка завантаження файлу',
        'error'
      );
    }
  };

  const handleSearch = async (query: string) => {
    setIsSearching(true);
    setSearchResults([]);
    
    try {
      const response = await fetch(`${API_BASE_URL}/search-media`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      
      if (response.ok) {
        setSearchResults(data);
        showNotification(`Знайдено ${data.length} результатів`, 'success');
      } else {
        throw new Error(data.detail || 'Помилка пошуку');
      }
    } catch (error) {
      console.error('Error searching media:', error);
      showNotification(
        error instanceof Error ? error.message : 'Помилка пошуку',
        'error'
      );
    } finally {
      setIsSearching(false);
    }
  };

  const theme = createTheme({
    palette: {
      mode: 'light',
      primary: {
        main: '#1976d2',
      },
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <NewspaperIcon sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Медіа Сканер
            </Typography>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ mt: 4 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Пошук" />
              <Tab label="Джерела" />
              <Tab label="Імпорт CSV" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <SearchMedia onSearch={handleSearch} isLoading={isSearching} />
            <Box sx={{ mt: 2 }}>
              <SearchResults results={searchResults} />
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <SourcesList />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <FileUpload onFileUpload={handleFileUpload} />
          </TabPanel>
        </Container>
      </Box>
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.type}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
}

export default App;

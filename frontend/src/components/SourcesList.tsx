import React, { useEffect, useState } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  Tabs,
  Tab,
} from '@mui/material';

interface Source {
  domain: string;
  name: string;
  url: string;
  created_at?: string;
  found_at?: string;
}

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

const SourcesList: React.FC = () => {
  const [knownSources, setKnownSources] = useState<Source[]>([]);
  const [newSources, setNewSources] = useState<Source[]>([]);
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  useEffect(() => {
    // Завантаження відомих джерел
    fetch('http://localhost:8000/api/v1/known-sources')
      .then(response => response.json())
      .then(data => setKnownSources(Array.isArray(data) ? data : []))
      .catch(error => {
        console.error('Error fetching known sources:', error);
        setKnownSources([]);
      });

    // Завантаження нових джерел
    fetch('http://localhost:8000/api/v1/new-sources')
      .then(response => response.json())
      .then(data => setNewSources(Array.isArray(data) ? data : []))
      .catch(error => {
        console.error('Error fetching new sources:', error);
        setNewSources([]);
      });
  }, []);

  const renderSourcesTable = (sources: Source[]) => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Домен</TableCell>
            <TableCell>Назва</TableCell>
            <TableCell>URL</TableCell>
            <TableCell>Дата</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(Array.isArray(sources) ? sources : []).map((source, index) => (
            <TableRow key={index}>
              <TableCell>{source.domain}</TableCell>
              <TableCell>{source.name}</TableCell>
              <TableCell>
                <a href={source.url} target="_blank" rel="noopener noreferrer">
                  {source.url}
                </a>
              </TableCell>
              <TableCell>
                {source.created_at || source.found_at || 'Невідомо'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Відомі джерела" />
          <Tab label="Нові джерела" />
        </Tabs>
      </Box>
      
      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" gutterBottom>
          Відомі джерела ({knownSources.length})
        </Typography>
        {renderSourcesTable(knownSources)}
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          Нові знайдені джерела ({newSources.length})
        </Typography>
        {renderSourcesTable(newSources)}
      </TabPanel>
    </Box>
  );
};

export default SourcesList; 
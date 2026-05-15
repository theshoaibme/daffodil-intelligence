import React from 'react';
import { Box } from '@mui/material';
import { motion } from 'framer-motion';

const GoogleSpinner: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{
          duration: 1,
          repeat: Infinity,
          ease: "linear"
        }}
        style={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          border: '4px solid rgba(66, 133, 244, 0.1)',
          borderTop: '4px solid #4285F4',
          borderRight: '4px solid #EA4335',
          borderBottom: '4px solid #FBBC05',
          borderLeft: '4px solid #34A853',
        }}
      />
    </Box>
  );
};

export default GoogleSpinner;

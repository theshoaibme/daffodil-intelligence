import React from 'react';
import { Box, Stack } from '@mui/material';
import { motion } from 'framer-motion';

const GoogleLoader: React.FC = () => {
  const colors = ['#4285F4', '#EA4335', '#FBBC05', '#34A853'];

  return (
    <Stack direction="row" spacing={1} justifyContent="center" alignItems="center">
      {colors.map((color, index) => (
        <motion.div
          key={color}
          animate={{
            opacity: [0.3, 1, 0.3]
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: index * 0.15,
            ease: "easeInOut"
          }}
        >
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              bgcolor: color,
              boxShadow: `0 0 10px ${color}40`
            }}
          />
        </motion.div>
      ))}
    </Stack>
  );
};

export default GoogleLoader;

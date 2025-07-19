import React from 'react';
import { PieChart, Pie, Cell, Tooltip } from 'recharts';

const PingChart = ({ data }) => {
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  return (
    <div className="bg-white p-4 rounded shadow-lg">
      <h2 className="text-xl font-bold mb-4">📊 Resource Usage</h2>
      <PieChart width={400} height={400}>
        <Pie
          data={data}
          cx={200}
          cy={200}
          innerRadius={60}
          outerRadius={80}
          fill="#8884d8"
          paddingAngle={5}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </div>
  );
};

export default PingChart;
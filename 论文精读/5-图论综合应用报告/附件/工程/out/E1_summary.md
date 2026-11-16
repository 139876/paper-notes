### E1 最短路算法交叉验证

| 指标 | 结果 | 判定 |
|---|---|---|
| 顶点数 \|V\| / 边数 \|E\| | 23 / 26 | - |
| 图连通性 | 连通 | PASS |
| Dijkstra vs NetworkX 最大偏差 | 0.000e+00 | PASS |
| Floyd vs Dijkstra 最大偏差 | 2.274e-13 | PASS |
| 配送距离矩阵 vs NetworkX 最大偏差 | 0.000e+00 | PASS |
| 割边（桥）数量 | 7  ['EA02', 'EA03', 'EA04', 'EA05', 'EA06', 'EA07', 'EA01'] | 第 5.6 节封闭实验候选 |
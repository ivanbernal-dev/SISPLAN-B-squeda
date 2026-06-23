// frontend/src/router/index.ts
// Agregar al arreglo de children protegido por AdminLayout.

{
  path: 'comite-directivo',
  name: 'comite-directivo',
  component: () => import(
    '@/modules/comite-directivo/views/IndicadoresComiteDirectivoView.vue'
  ),
  meta: {
    title: 'Comité Directivo',
    roles: ['ADMIN', 'OAP', 'DIRECTIVO', 'CONSULTA'],
    readOnly: true,
  },
},

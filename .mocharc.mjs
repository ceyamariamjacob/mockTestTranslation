// .mocharc.mjs (ESM version)
export default {
  require: 'ts-node/register',
  extension: ['ts'],
  spec: 'test/**/*.test.ts',
  timeout: 5000
};

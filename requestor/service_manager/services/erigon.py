import json

from .erigon_payload import ErigonPayload

from yapapi.executor.services import Service


class Erigon(Service):
    @classmethod
    async def get_payload(cls):
        return ErigonPayload()

    async def start(self):
        yield self._ctx.commit()

    async def run(self):
        while True:
            service_signal = await self._listen()
            command = service_signal.message
            if command == 'STATUS':
                self._ctx.run(command)
                try:
                    processing_future = yield self._ctx.commit()
                    result = self._parse_status_result(processing_future.result())
                    self._respond_nowait(result, service_signal)
                except Exception as e:
                    result = {'status': f'FAILED: {e}'}
                    self._respond_nowait(result, service_signal)
                    break
            elif command == 'STOP':
                result = {'status': 'STOPPING'}
                self._respond_nowait(result, service_signal)
                break

    def _parse_status_result(self, raw_data):
        #   NOTE: raw_data contains also output from "start" and "deploy" for the first
        #         request, and only single row for subsequent requests -> that's why -1 not 0
        command_executed = raw_data[-1]

        stdout = command_executed.stdout
        mock_echo_data, erigon_data = stdout.split('ERIGON: ', 2)
        erigon_data = json.loads(erigon_data)
        return erigon_data

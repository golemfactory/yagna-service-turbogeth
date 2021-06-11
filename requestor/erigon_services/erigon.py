import json
import asyncio

from .erigon_payload import ErigonPayload

from yapapi.services import Service

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from yapapi.executor.events import CommandExecuted


class Erigon(Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = None
        self.auth = None

        #   NOTE: this is the network provider says it is running on, not the one
        #         requested (although those two should match)
        self.network = None

    @classmethod
    async def get_payload(cls):
        return ErigonPayload()

    async def start(self):
        self._ctx.deploy()
        self._ctx.start('{"network": "kovan"}')
        yield self._ctx.commit()

    async def run(self):
        #   Set url & auth
        self._ctx.run('STATUS')
        processing_future = yield self._ctx.commit()
        result = self._parse_status_result(processing_future.result())
        self.url, self.auth, self.network = result['url'], result['auth'], result['network']

        #   Wait forever, because Service is stopped when run ends
        await asyncio.Future()

    def _parse_status_result(self, raw_data: 'List[CommandExecuted]'):
        #   NOTE: raw_data contains also output from "start" and "deploy" for the first
        #         request, and only single row for subsequent requests -> that's why -1 not 0
        command_executed = raw_data[-1]

        stdout = command_executed.stdout
        mock_echo_data, erigon_data = stdout.split('ERIGON: ', 2)
        erigon_data = json.loads(erigon_data)
        return erigon_data

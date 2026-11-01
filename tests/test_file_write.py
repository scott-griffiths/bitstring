import io

import pytest

from bitstring import Array, Bits, BitArray


@pytest.mark.parametrize('kind', [Bits, BitArray, lambda data: Array.from_bytes('u8', data.to_bytes())])
@pytest.mark.parametrize('chunk_size', [1, 2, 3])
def test_to_file_completes_short_writes(kind, chunk_size):
    class PartialWriter(io.BytesIO):
        def write(self, data):
            return super().write(data[:chunk_size])

    source = kind(Bits('0x0123456789ab'))
    destination = PartialWriter()
    source.to_file(destination)
    assert destination.getvalue() == source.to_bytes()


@pytest.mark.parametrize('kind', [Bits, BitArray])
def test_to_file_pads_only_the_last_byte(kind):
    class PartialWriter(io.BytesIO):
        def write(self, data):
            return super().write(data[:1])

    source = kind('0b10101010101')
    destination = PartialWriter()
    source.to_file(destination)
    assert destination.getvalue() == b'\xaa\xa0'


@pytest.mark.parametrize('result', [0, None])
def test_to_file_rejects_writes_without_progress(result):
    class StalledWriter(io.BytesIO):
        def write(self, data):
            return result

    with pytest.raises(BlockingIOError):
        Bits('0x1234').to_file(StalledWriter())


def test_to_file_propagates_write_errors():
    failure = OSError('storage unavailable')

    class FailingWriter(io.BytesIO):
        def write(self, data):
            raise failure

    with pytest.raises(OSError) as caught:
        Bits('0x1234').to_file(FailingWriter())
    assert caught.value is failure

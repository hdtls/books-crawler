
class DecodingError(Exception):
    """Encoding error"""

def type_mismatch(item, path, expectation, reality):
    return DecodingError(f"{type(item)} typeMismatch({expectation} codingPath: {path} debugDescription: 'Expected to decode {expectation} but found a {type(reality)} instead.')")

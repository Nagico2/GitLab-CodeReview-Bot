import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SRC_ROOT = ROOT / 'src'

sys.path.append(ROOT.as_posix())
sys.path.append(SRC_ROOT.as_posix())


from config.config import api_config as out_config
from llm_api.load_api import create_llm_api_instance


if __name__ == "__main__":
    api = create_llm_api_instance()
    api.set_config(out_config)
    api.generate_text([
        {"role": "system",
         "content": "你是一位作家"
         },
        {"role": "user",
         "content": "请写一首抒情的诗",
         }
    ])
    print(api.get_respond_content())
    print(api.get_respond_tokens())

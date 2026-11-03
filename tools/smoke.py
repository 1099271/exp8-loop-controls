import sys, time
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
ck = sys.argv[1]
def main():
    tok = AutoTokenizer.from_pretrained(ck)
    t = time.time()
    llm = LLM(model=ck, dtype="bfloat16", gpu_memory_utilization=0.85, max_model_len=32768 + 2048, seed=0, language_model_only=True)
    print("load s", round(time.time() - t))
    for th in (False, True):
        p = tok.apply_chat_template([{"role": "user", "content": "What is 17*23?\nPlease reason step by step, and put your final answer within \\boxed{}."}],
                                    tokenize=False, add_generation_prompt=True, enable_thinking=th)
        print("PROMPT_TAIL", repr(p[-60:]))
        o = llm.generate([p], SamplingParams(temperature=0.6, top_p=0.95, top_k=20, presence_penalty=1.5, max_tokens=1024, seed=0))[0].outputs[0]
        print("thinking", th, o.finish_reason, len(o.token_ids), repr(o.text[-200:]))


if __name__ == "__main__":
    main()

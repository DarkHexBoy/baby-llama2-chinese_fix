import os
import json
import torch
from tqdm import tqdm
import numpy as np
from transformers import (
    PreTrainedModel,
    PreTrainedTokenizerBase,
)

class CEval:
    DATA_PATH = "ceval/ceval-exam"
    TASK2DESC = {
        "high_school_physics": "高中物理",
        "fire_engineer": "注册消防工程师",
        "computer_network": "计算机网络",
        "advanced_mathematics": "高等数学",
        "logic": "逻辑学",
        "middle_school_physics": "初中物理",
        "clinical_medicine": "临床医学",
        "probability_and_statistics": "概率统计",
        "ideological_and_moral_cultivation": "思想道德修养与法律基础",
        "operating_system": "操作系统",
        "middle_school_mathematics": "初中数学",
        "chinese_language_and_literature": "中国语言文学",
        "electrical_engineer": "注册电气工程师",
        "business_administration": "工商管理",
        "high_school_geography": "高中地理",
        "modern_chinese_history": "近代史纲要",
        "legal_professional": "法律职业资格",
        "middle_school_geography": "初中地理",
        "middle_school_chemistry": "初中化学",
        "high_school_biology": "高中生物",
        "high_school_chemistry": "高中化学",
        "physician": "医师资格",
        "high_school_chinese": "高中语文",
        "tax_accountant": "税务师",
        "high_school_history": "高中历史",
        "mao_zedong_thought": "毛泽东思想和中国特色社会主义理论概论",
        "high_school_mathematics": "高中数学",
        "professional_tour_guide": "导游资格",
        "veterinary_medicine": "兽医学",
        "environmental_impact_assessment_engineer": "环境影响评价工程师",
        "basic_medicine": "基础医学",
        "education_science": "教育学",
        "urban_and_rural_planner": "注册城乡规划师",
        "middle_school_biology": "初中生物",
        "plant_protection": "植物保护",
        "middle_school_history": "初中历史",
        "high_school_politics": "高中政治",
        "metrology_engineer": "注册计量师",
        "art_studies": "艺术学",
        "college_economics": "大学经济学",
        "college_chemistry": "大学化学",
        "law": "法学",
        "sports_science": "体育学",
        "civil_servant": "公务员",
        "college_programming": "大学编程",
        "middle_school_politics": "初中政治",
        "teacher_qualification": "教师资格",
        "computer_architecture": "计算机组成",
        "college_physics": "大学物理",
        "discrete_mathematics": "离散数学",
        "marxism": "马克思主义基本原理",
        "accountant": "注册会计师",
    }

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizerBase,
        opt,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.opt = opt

    def run(self, data_path, shot: int, logger):
        results, accs = {}, {}

        dir_name = os.path.splitext(self.opt.save_path)[0]+'_Ceval'
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        # run all task
        for task_name in self.TASK2DESC:
            print("=" * 100)
            print(f"run task: {task_name}")
            result, acc = self.run_single_task(data_path, task_name, shot)
            results[task_name] = result
            accs[task_name] = acc

            result_path = os.path.join(dir_name, f"{task_name}.json")
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"save result to {result_path}")

        average_acc = sum(accs.values()) / len(accs)
        accs['average'] = average_acc

        # results
        acc_path = os.path.join(dir_name, "ceval_acc.json")
        with open(acc_path, "w") as f:
            json.dump(accs, f, indent=2)
        print(f"Ceval average acc: {average_acc}\n")

        logger.info(f'model: {self.opt.save_path}. Ceval_eval_scores: {average_acc}')
        return average_acc

    def run_single_task(self, data_path, task_name: str, shot: int):
        import os
        dataset = dict()
        if os.path.exists(data_path):
            import os
            import pandas as pd
            for name in ('val', 'dev'):
                csv_data = pd.read_csv(
                    os.path.join(os.path.join(data_path, name), task_name + '_' + name + '.csv'))
                questions = []
                for idx in range(len(csv_data)):
                    data_que = dict()
                    data_que["id"] = csv_data.id[idx]
                    data_que["question"] = csv_data.question[idx]
                    data_que["A"] = csv_data.A[idx]
                    data_que["B"] = csv_data.B[idx]
                    data_que["C"] = csv_data.C[idx]
                    data_que["D"] = csv_data.D[idx]
                    data_que["answer"] = csv_data.answer[idx]
                    questions.append(data_que)

                dataset[name] = questions
        else:
            from datasets import load_dataset
            dataset = load_dataset(self.DATA_PATH, task_name)

        # tmp_ = dataset[split]
        results = []
        acc = 0

        for data in tqdm(dataset['val']):
            prompt = f"以下是中国关于{self.TASK2DESC[task_name]}考试的单项选择题，请选出其中的正确答案。\n"
            if shot != 0:
                if isinstance(dataset["dev"], list):
                    import random
                    random.shuffle(dataset["dev"])
                    shuffled = dataset["dev"]
                else:
                    shuffled = dataset["dev"].shuffle()
                for i in range(min(shot, len(shuffled))):
                    prompt += "\n" + self.build_example(shuffled[i], with_answer=True)
            prompt += "\n" + self.build_example(data, with_answer=False)

            # input_ids = self.tokenizer.encode(prompt, return_tensors="pt").cuda()
            # logits = self.model(
            #         input_ids=input_ids,
            #     ).logits[:,-1].flatten()

            x=self.tokenizer.encode(prompt,add_special_tokens=False)+[self.tokenizer.special_tokens['<eos>']]
            x = (torch.tensor(x, dtype=torch.long, device=self.opt.device)[None, ...])
            logits = self.model(x)[0][0]

            candidate_logits = [logits[self.tokenizer(label,add_special_tokens=False).input_ids[-1]] for label in ["A", "B", "C", "D"]]
            candidate_logits = torch.tensor(candidate_logits).to(torch.float32)
            probs = (
                torch.nn.functional.softmax(
                    candidate_logits,
                    dim=0,
                )
                .detach()
                .cpu()
                .numpy()
            )
            answer = {i: k for i, k in enumerate(["A", "B", "C", "D"])}[np.argmax(probs)]

            results.append(
                {
                    "prompt": prompt,
                    "correct": answer == data["answer"].strip().upper(),
                    "answer": answer,
                }
            )
            acc += answer == data["answer"].strip().upper()
        acc /= len(dataset['val'])
        return results, acc

    def build_example(self, data, with_answer: bool = True):
        question = data["question"]
        choice = "\n".join(
            [
                "A. " + data["A"],
                "B. " + data["B"],
                "C. " + data["C"],
                "D. " + data["D"],
            ]
        )
        answer = data["answer"].strip().upper() if with_answer else ""
        return f"{question}\n{choice}\n答案: {answer}"
    
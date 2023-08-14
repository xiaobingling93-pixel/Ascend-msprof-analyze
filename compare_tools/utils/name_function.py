from utils.torch_op_node import TorchOpNode


class NameFunction:
    def __init__(self, args: any):
        self.args = args

    @classmethod
    def get_name(cls, op_node: TorchOpNode) -> str:
        return op_node.name

    @classmethod
    def get_full_name(cls, op_node: TorchOpNode) -> str:
        if isinstance(op_node.origin_input_shape, list):
            data = []
            for dim in op_node.origin_input_shape:
                data.append(','.join([str(x) for x in dim]))
            input_shape = ';\r\n'.join(data)
            return f'{op_node.name}{input_shape}'
        return f'{op_node.name}{op_node.input_shape}'

    def get_name_func(self):
        if not self.args.op_name_map and not self.args.use_input_shape:
            name_func = self.get_name
        elif self.args.op_name_map and not self.args.use_input_shape:
            name_func = self.get_map_name
        elif self.args.op_name_map and not self.args.use_input_shape:
            name_func = self.get_full_name
        else:
            name_func = self.get_full_map_name
        return name_func

    def get_map_name(self, op_node: TorchOpNode) -> str:
        return self.args.op_name_map.get(op_node.name, op_node.name)

    def get_full_map_name(self, op_node: TorchOpNode) -> str:
        if isinstance(op_node.origin_input_shape, list):
            data = []
            for dim in op_node.origin_input_shape:
                data.append(','.join([str(x) for x in dim]))
            input_shape = ';\r\n'.join(data)
            return f'{self.args.op_name_map.get(op_node.name, op_node.name)}{input_shape}'
        return f'{self.args.op_name_map.get(op_node.name, op_node.name)}{op_node.input_shape}'

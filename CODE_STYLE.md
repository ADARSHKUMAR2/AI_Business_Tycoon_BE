# Code Styles and Quality

- Every C# file under `Assets/Source/` gets a namespace matching its directory relative to `Source` (e.g. `Source/Player/Combat` → `namespace Source.Player.Combat`).
- Unless specified otherwise, assume every component is an empty class. Do not add methods, properties or fields.
- Prefer to define properties as public with private setters.
- Prefer using events over polling when working with Unity’s input system.
- Private fields should be prefixed with an `_` character.
- Fields or properties storing a component should be suffixed with `Component`. For example, if a field is storing an `Animator` component, the field should be called `_animatorComponent`.
- Prefer to use hash IDs when working with animator parameters. Store the IDs in readonly fields.
- Prefer to use `OnSetup()` for setting up components in the `Unity.Behavior.Action` class.
- Prefer guard clauses over nested conditionals.
- Prefer `UnityAction` over `Action`, including for event types; always use the `event` keyword.
- Every event gets a static `Raise<EventName>()` invoker method; handlers are named `On<EventName>`.
- Do not update the scene in the game unless explicitily told to do so.
- create editor scripts for all components and prefabs, dont create them in the code.